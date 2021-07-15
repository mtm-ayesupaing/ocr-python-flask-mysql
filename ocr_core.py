from tesserocr import PyTessBaseAPI

def ocr_core(filename):
    with PyTessBaseAPI(path='./tessdata/.', lang='eng') as api:
        print("HELLO IMAGE :: ", filename)
        api.SetImageFile(filename)
        print(api.GetUTF8Text())
        text = api.GetUTF8Text()
    return text