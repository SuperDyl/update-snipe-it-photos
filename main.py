import _io
import requests
import os
from base64 import b64encode
from pathlib import Path
import shutil

API_URL: str = 'https://byu.snipe-it.io/api/v1'
TOKEN: str = ''
HEADERS: dict = {'Authorization': f'Bearer {TOKEN}',
                 'Accept': 'application/json',
                 'Content-Type': 'application/json'
                 }


def get_asset(asset_id: int):
    return requests.get(API_URL + '/hardware/' + str(asset_id), headers=HEADERS)


def get_hardware_by_model(model_id: str) -> requests.Response:
    return requests.get(API_URL + '/hardware', headers=HEADERS, params={'model_id': model_id})


def put_image(asset_id: int,
              asset_tag: str,
              status_id: int,
              model_id: int,
              file_path: str) -> requests.Response:
    path = Path(file_path)
    img_extension = path.suffix[1:].lower()
    if img_extension == 'jpg':
        img_extension = 'jpeg'
    file_name = path.name

    with open(file_path, 'rb') as file:
        img_base64 = b64encode(file.read()).decode()

        print(f"data:image/{img_extension};name={file_name};base64,{img_base64}")

        # print(img_base64[0:20], img_base64[-20:])

        request_body = {
            'asset_tag': asset_tag,
            'status_id': status_id,
            'model_id': model_id,
            "image": f"data:image/{img_extension};name={file_name};base64,{img_base64}"
        }

    return requests.put(
        API_URL + '/hardware/' + str(asset_id),
        json=request_body,
        headers=HEADERS)


def put_image_as_asset(asset: dict, file) -> requests.Response:
    return put_image(
        asset['id'],
        asset['asset_tag'],
        asset['status_label']['id'],
        asset['model']['id'],
        file
    )


def post_model_image(model_id: str, file) -> None:
    # Search for assets with the specified model number
    response = get_hardware_by_model(model_id)
    response.raise_for_status()

    assets = response.json()

    # Update each asset with the picture from the specified file
    for asset in assets:
        response = put_image_as_asset(asset, file)
        response.raise_for_status()


def update_model_image(dir_item: os.DirEntry) -> None:
    if not dir_item.is_file():
        return

    post_model_image(dir_item.name, dir_item.path)


def update_model_images(src_dir: str, out_dir: str) -> None:
    with os.scandir(src_dir) as dir_items:
        item: os.DirEntry
        for item in dir_items:
            try:
                update_model_image(item)
            except requests.exceptions.HTTPError:
                print(f'Failed to add post images for {item.name}!')
            else:
                shutil.move(item, out_dir)


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
