import cloudinary.uploader
from flask import current_app

def upload_media(file, folder="general"):
    """Upload file to Cloudinary"""
    try:
        # Determine resource type
        resource_type = 'video' if file.content_type.startswith('video/') else 'image'
        
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type,
            transformation=[
                {'width': 800, 'height': 800, 'crop': 'limit'},
                {'quality': 'auto'}
            ] if resource_type == 'image' else None
        )
        
        return result
        
    except Exception as e:
        raise Exception(f"Upload failed: {str(e)}")

def delete_media(public_id, resource_type='image'):
    """Delete file from Cloudinary"""
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result
    except Exception as e:
        raise Exception(f"Delete failed: {str(e)}") 
