"""
Social Router
==============
Endpoints: feed, create post, like/comment on posts.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
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

    if not result and page == 1:
        # Fallback to mock data if feed is empty
        result = [
            {
                "id": "mock-feed-1",
                "user": {"id": "u1", "name": "Chef Mike", "avatar_url": ""},
                "recipe_id": "trending-shivamogga-0",
                "recipe_title": "Spicy Fusion Pasta",
                "content": "Just tried the new AI recipe! Substituted basil with spinach, and it turned out insanely good! 🍝",
                "image_url": "https://images.unsplash.com/photo-1473093295043-cdd812d0e601?auto=format&fit=crop&w=800&q=80",
                "likes_count": 24,
                "comments_count": 3,
                "is_liked": False,
                "created_at": str(datetime.now(timezone.utc)),
            },
            {
                "id": "mock-feed-2",
                "user": {"id": "u2", "name": "Sarah Cooks", "avatar_url": ""},
                "recipe_id": "trending-shivamogga-1",
                "recipe_title": "15-Min Healthy Bowl",
                "content": "Saved 3 carrots and half an onion from going bad thanks to the waste tracker. Feeling like an absolute eco-warrior today 🌱",
                "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=800&q=80",
                "likes_count": 89,
                "comments_count": 12,
                "is_liked": True,
                "created_at": str(datetime.now(timezone.utc)),
            }
        ]

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
    try:
        post = await db.social_posts.find_one({"_id": ObjectId(post_id)})
    except InvalidId:
        # User liked a mock fallback post, pretend it worked
        return {"liked": True, "mock": True}

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

    try:
        obj_id = ObjectId(post_id)
    except InvalidId:
        return {"comment_id": str(comment["_id"]), "mock": True}

    result = await db.social_posts.update_one(
        {"_id": obj_id},
        {"$push": {"comments": comment}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Post not found")

    return {"comment_id": str(comment["_id"])}
