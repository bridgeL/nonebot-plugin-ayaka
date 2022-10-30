from ayaka import AyakaApp

app = AyakaApp("复读")
app.help = "每三次就复读一次，复读过的不再复读"


@app.on.on_idle()
@app.on.text()
async def repeat():
    '''监听一下'''
    s = str(app.arg)
    if app.cache.last == s:
        if app.cache.cnt is None:
            app.cache.cnt = 0
        app.cache.cnt += 1
    else:
        app.cache.cnt = 0
    app.cache.last = s

    if app.cache.cnt == 2:
        await app.send(s)
