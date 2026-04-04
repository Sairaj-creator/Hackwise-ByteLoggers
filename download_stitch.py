import urllib.request
import os

files = {
    "Settings.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzVhMGIxYjBmYTZkYzQzMzFiOGFmOWRmNzgxZjJiNzRiEgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "Recipe_Details_Updated.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzljMTc4YTRmNGUwNzQ2YTdhZGQyZjUyMGJiMDgxMjNjEgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "Visual_Scanner.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzdmMDRmMmE0ZDJmZDRkMjc4OGMwYTIzZjA1OTM1YWE5EgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "Ingredient_Benefits.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2RkNmZhZDllNWU2MTRmNTRiMDRlYjg3MDdiMmU3MzU0EgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "Fridge_with_In-line_Recipes.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2RkZjI5MWI2NDJjYzRhYzNhMzQwOGE1MDBmYjRkOTVlEgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "Home_Feed_Updated.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzQzMDM4MzI3YThjODQzM2E4ZDc5M2VhNWI2YzUxZmQ1EgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "Landing_Page.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzVhNmYyZmU0ZjYyMjQ1YTJiMWQ1YjFmYzM1MDA4ZGI5EgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "My_Fridge.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzNkOTdkNjdjYzc2MjRjZDlhM2JjZDZhZWM3OGM5OTc2EgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086",
    "My_Digital_Fridge_Clean.html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzNlMTdlOTY2MzQxYTRkZTU5Y2EzZDE5ZTZkOTkxOWRhEgsSBxCy77nl_BgYAZIBJAoKcHJvamVjdF9pZBIWQhQxNDIxNzY4MTU5OTAxMjg3NTc2OQ&filename=&opi=89354086"
}

out_dir = r"d:\Hackwise-ByteLoggers\stitch_htmls"
os.makedirs(out_dir, exist_ok=True)

for name, url in files.items():
    print(f"Downloading {name}...")
    try:
        urllib.request.urlretrieve(url, os.path.join(out_dir, name))
        print(f"Saved {name}")
    except Exception as e:
        print(f"Error downloading {name}: {e}")
