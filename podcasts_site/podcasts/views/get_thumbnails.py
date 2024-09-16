def get_thumbnails(information):
    thumbnail = information.get('thumbnail', None)
    if thumbnail is None:
        pass
    if ".png" in thumbnail:
        return thumbnail[:thumbnail.index(".png") + 4]
    elif ".jpg" in thumbnail:
        return thumbnail[:thumbnail.index(".jpg") + 4]
    else:
        return None