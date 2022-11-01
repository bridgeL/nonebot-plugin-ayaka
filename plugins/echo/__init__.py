from ayaka import AyakaApp

app = AyakaApp("复读")
app.help = "每三次就复读一次，复读过的不再复读"


@app.on.idle()
@app.on.text()
async def repeat():
    '''监听一下'''
    s = str(app.arg)
    uid = app.user_id
    if app.cache.last != s:
        app.cache.uids = [uid]
        app.cache.last = s
        return

    if uid not in app.cache.uids:
        app.cache.uids.append(uid)
        if len(app.cache.uids) == 3:
            await app.send(s)
