from requests import Response, exceptions
import os
from base64 import b64encode
from pathlib import Path
import shutil
from ratelimiter import RateLimiter

API_URL: str = 'https://byu.snipe-it.io/api/v1'
TOKEN: str = ''
HEADERS: dict = {'Authorization': f'Bearer {TOKEN}',
                 'Accept': 'application/json',
                 'Content-Type': 'application/json'
                 }
reqs = RateLimiter(API_URL, time_limit=60, request_limit=120)


def get_models(model_name: str) -> Response:
    return reqs.get('/models', headers=HEADERS, params={'search': model_name})


def get_asset(asset_id: int) -> Response:
    return reqs.get('/hardware/' + str(asset_id), headers=HEADERS)


def get_hardware_by_model(model_id: int) -> Response:
    return reqs.get('/hardware', headers=HEADERS, params={'model_id': model_id})


def put_image(asset_id: int,
              asset_tag: str,
              status_id: int,
              model_id: int,
              file_path: str) -> Response:
    path = Path(file_path)
    img_extension = path.suffix[1:].lower()
    if img_extension == 'jpg':
        img_extension = 'jpeg'
    file_name = path.name

    with open(file_path, 'rb') as file:
        img_base64 = b64encode(file.read()).decode()
        # print(f"data:image/{img_extension};name={file_name};base64,{img_base64}")
        # print(img_base64[0:20], img_base64[-20:])

        request_body = {
            'asset_tag': asset_tag,
            'status_id': status_id,
            'model_id': model_id,
            "image": f"data:image/{img_extension};name={file_name};base64,{img_base64}"
        }

    return reqs.put(
        '/hardware/' + str(asset_id),
        json=request_body,
        headers=HEADERS)


def put_image_as_asset(asset: dict, file) -> Response:
    return put_image(
        asset['id'],
        asset['asset_tag'],
        asset['status_label']['id'],
        asset['model']['id'],
        file
    )


def post_model_image(model_id: int, file) -> bool:
    # Search for assets with the specified model number
    response = get_hardware_by_model(model_id)
    response.raise_for_status()

    assets = response.json()
    if assets['total'] == 0:
        return False

    # Update each asset with the picture from the specified file
    for asset in assets['rows']:
        response = put_image_as_asset(asset, file)
        response.raise_for_status()

    return True


def update_model_image(dir_item: os.DirEntry) -> bool:
    if not dir_item.is_file():
        return False

    file_name: str = str(Path(dir_item.name).with_suffix(''))
    response: Response = get_models(file_name)
    if not response.ok:
        print(f'Error finding model for name {file_name}')
        return False

    search_rows: dict = response.json()
    if not search_rows:
        return False

    models: list = search_rows['rows']
    if not models:
        return False
    model_id: int = models[0]['id']
    return post_model_image(model_id, dir_item.path)


def update_model_images(src_dir: str, out_dir: str) -> None:
    with os.scandir(src_dir) as dir_items:
        item: os.DirEntry
        for item in dir_items:
            try:
                if update_model_image(item):
                    shutil.move(item, out_dir)
            except exceptions.HTTPError as error:
                print(f'Failed to add post images for {item.name}!')
                print(error)


def safe_mkdir(path: str):
    standard_path: Path = Path(path)

    if not standard_path.exists():
        os.mkdir(standard_path)
    elif standard_path.is_file():
        raise IOError(f'Cannot create directory {standard_path}. Item already exists as a file')


if __name__ == '__main__':
    INPUT: str = './model_images'
    OUTPUT: str = './finished_images'

    safe_mkdir(INPUT)
    safe_mkdir(OUTPUT)

    update_model_images(INPUT, OUTPUT)
