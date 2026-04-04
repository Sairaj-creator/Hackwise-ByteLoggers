"""
Social Router
==============
Endpoints: feed, create post, like/comment on posts.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional

from app.dependencies import get_current_user
from app.database.mongodb import get_database

router = APIRouter(prefix="/api/v1/social", tags=["Social"])


# ─── Feed ───

@router.get("/feed")
async def get_feed(
    page: int = 1,
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    db = get_database()
    skip = (page - 1) * limit

    posts = await db.social_posts.find().sort(
        "created_at", -1
    ).skip(skip).limit(limit + 1).to_list(length=limit + 1)

    has_more = len(posts) > limit
    posts = posts[:limit]

    result = []
    for post in posts:
        author = await db.users.find_one({"_id": post["user_id"]})
        recipe = None
        if post.get("recipe_id"):
            recipe = await db.recipes.find_one({"_id": post["recipe_id"]})

        result.append({
            "id": str(post["_id"]),
            "user": {
                "id": str(post["user_id"]),
                "name": author.get("name", "Unknown") if author else "Unknown",
                "avatar_url": "",
            },
            "recipe_id": str(post["recipe_id"]) if post.get("recipe_id") else None,
            "recipe_title": recipe.get("title", "") if recipe else "",
            "content": post.get("content", ""),
            "image_url": post.get("image_url", ""),
            "likes_count": post.get("likes_count", 0),
            "comments_count": len(post.get("comments", [])),
            "is_liked": user["_id"] in post.get("likes", []),
            "created_at": str(post.get("created_at", "")),
        })

    return {
        "posts": result,
        "has_more": has_more,
        "next_page": page + 1 if has_more else None,
    }


# ─── Create Post ───

@router.post("/posts")
async def create_post(
    recipe_id: str = Form(default=""),
    content: str = Form(default=""),
    image: Optional[UploadFile] = File(default=None),
    user: dict = Depends(get_current_user),
):
    db = get_database()

    image_url = ""
    # TODO: upload image to Cloudinary in production

    post_doc = {
        "user_id": user["_id"],
        "recipe_id": ObjectId(recipe_id) if recipe_id else None,
        "content": content,
        "image_url": image_url,
        "likes": [],
        "likes_count": 0,
        "comments": [],
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.social_posts.insert_one(post_doc)

    return {"post_id": str(result.inserted_id)}


# ─── Like Post ───

@router.post("/posts/{post_id}/like")
async def toggle_like(post_id: str, user: dict = Depends(get_current_user)):
    db = get_database()
    post = await db.social_posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(404, "Post not found")

    if user["_id"] in post.get("likes", []):
        await db.social_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$pull": {"likes": user["_id"]}, "$inc": {"likes_count": -1}},
        )
        return {"liked": False}
    else:
        await db.social_posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$addToSet": {"likes": user["_id"]}, "$inc": {"likes_count": 1}},
        )
        return {"liked": True}


# ─── Comment on Post ───

@router.post("/posts/{post_id}/comment")
async def add_comment(
    post_id: str,
    text: str = Form(...),
    user: dict = Depends(get_current_user),
):
    db = get_database()
    comment = {
        "_id": ObjectId(),
        "user_id": user["_id"],
        "text": text,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.social_posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$push": {"comments": comment}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Post not found")

    return {"comment_id": str(comment["_id"])}
