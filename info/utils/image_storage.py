from qiniu import Auth, put_data

access_key = "jDi3-WkIrMcgwffmnVriC4rzGUfj1KF0m6ka6XW0"
secret_key = "dj-6wBnnZ0iiII0-ZEHqtoeBQgfquv7kJTZ_cDgs"
bucket_name = "ihome"


def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e;

    if info.status_code != 200:
        raise Exception("上传图片失败")
    return ret["key"]


if __name__ == '__main__':
    file = input('请输入文件路径')
    with open(file, 'rb') as f:
        storage(f.read())