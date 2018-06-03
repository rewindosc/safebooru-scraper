
from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from tqdm import tqdm
import urllib.request
import re
import os
import sys


def get_page(url):
    '''Request a page.

    If successfull, would return BeautifulSoup object, if not,
    would return None'''
    try:
        html = urlopen(url)
    except HTTPError:
        sys.exit("Can't load the page: \n{}".format(url))

    bs_obj = BeautifulSoup(html, "html.parser")
    try:
        bs_obj.h2
    except AttributeError:
        sys.exit("Can't load the page: \n{}".format(url))

    return bs_obj


def get_image_name(thumbnail_url, folder_id=False):
    '''Get name of an image from URL.

    folder_id -- if set to True, would return ID of the folder, in
    which image was stored on server.'''
    if folder_id:
        result = re.search(
            r'\/[0-9]*\/([A-Za-z0-9_]*)\.(png|gif|jpg|jpeg)', thumbnail_url)
        return re.sub(r'thumbnail_', '', result.group(0))
    else:
        return re.search(
            r'([A-Za-z0-9]*)\.(png|gif|jpg|jpeg)', thumbnail_url).group(0)


def download_image(url, directory='./'):
    '''Download image from url and save it to the directory.

    default directory -- script folder.'''
    return urllib.request.urlretrieve(
        url, "{}{}".format(directory, get_image_name(url)))


booru_url = 'https://safebooru.org/'

if __name__ == "__main__":
    while True:
        while True:
            print(
                'Please, enter a set of tags to search for (seperated by spaces):',
                end=' ')
            tags = input()

            # Should start with a-z0-9~-, contain only a-z0-9~- and spaces.
            match_tags = re.compile(r"^([a-z0-9_\-\~])+\s*([a-z0-9_\-\~\s])*$")
            if not tags or not re.match(match_tags, tags):
                print("\nYou should use at least 1 tag.")
                print("Tags can only contain a lowercase letters, digits, spaces.")
                print("Line should start with a lowercase letter or digit.\n")
            else:
                break

        tags = '+'.join([tag for tag in tags.split(' ')])
        bs_obj = get_page(booru_url + 'index.php?page=post&s=list&tags=' + tags)

        # If there's no result for that set of tags.
        if bs_obj.find("h1"):
            if bs_obj.find("h1").get_text() == "Nothing found, try google? ":
                print("\nNo result for \"" + tags + "\" tags.")
                print("Try other tags.\n")
        else:
            break

    while True:
        print('Choose name for the folder (/images/YOUR_NAME): ', end='')
        folder = input()

        # Should start with a-z0-9-_, no spaces.
        match_folder = re.compile(r"^[A-Za-z0-9_\-]*$")
        if folder.endswith('/') or not re.match(match_folder, folder):
            print("\nFolder path shouldn't end with \"/\" and ")
            print("can't contain spaces.\n")

            print(folder)
        else:
            break

    if not os.path.exists('./images/'):
        os.mkdir('./images/')

    print('Trying to create \"' + './images/' + folder + '/' + '\"...')
    try:
        os.mkdir('./images/' + folder + '/')
        print('Directory has been successfully created.')
    except FileExistsError:
        print('Directory already exist.')

    last_page = bs_obj.find("a", {"alt": "last page"})

    # last_page would be None, if there's only 1 page of images.
    if last_page is None:
        print("There is only 1 page of images.")

        for preview_image in tqdm(bs_obj.find_all("img", {"class": "preview"}),
                                  desc="Downloading..."):
            download_image(booru_url + "images" +
                           get_image_name(preview_image.attrs['src'], True),
                           './images/' + folder + '/')

    else:
        last_page = re.sub(r'^\?.*&pid=', '', last_page.attrs['href'])
        print("There are {} pages, ~{} files. "
              .format(int(last_page) / 40, last_page))

        pages = 0
        while True:
            print('How many pages do you want to download? (1 - {}): '
                  .format(int(last_page) / 40), end='')
            pages = int(input())

            if pages > (int(last_page) / 40) or pages < 1:
                print('\nInvalid number of pages. Please, choose between 1 - {}\n'
                      .format(int(last_page) / 40))
                continue
            else:
                break

        for page_id in tqdm(range(0, (pages * 40), 40), desc="Downloading..."):

            page = get_page(booru_url +
                            'index.php?page=post&s=list&tags=' +
                            tags +
                            "&pid=" + str(page_id)
                            )

            for preview_image in tqdm(page.find_all(
                    "img", {"class": "preview"}),
                    desc="Page #{}/{}".format(int(page_id / 40) + 1, pages),
                    unit_scale=True):
                download_image(booru_url + "images" +
                               get_image_name(preview_image.attrs['src'],
                                              True),
                               './images/' + folder + '/')

        print('\n')
