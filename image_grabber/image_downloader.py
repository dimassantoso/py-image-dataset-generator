import os
import urllib.request
import time

from .bing_grabber import BingGrabber
from .google_grabber import GoogleGrabber
from .grab_settings import *
from utils.string_utils import StringUtil
import math
import base64


class ImageDownloader:
    """Download images from a keyword and website sources"""

    keyword = None
    destination = DEFAULT_DESTINATION_FOLDER
    limit = DEFAULT_DOWNLOAD_LIMIT
    file_prefix = None
    image_size = ImageSize.LARGE

    sources = [DEFAULT_GRAB_SOURCE_TYPE]

    def __init__(self, destination=DEFAULT_DESTINATION_FOLDER, limit=DEFAULT_DOWNLOAD_LIMIT):
        """Constructor for ImageGrabber"""
        self.destination = destination
        self.limit = limit

    def download_images(self, keyword):
        start = time.time()

        if not keyword:
            raise Exception('No keyword to search')

        self.keyword = keyword
        self.__set_default_file_prefix()
        all_sources = [e.value for e in GrabSourceType]
        selected_sources = all_sources if ALL_SOURCE in self.sources else self.sources
        images = []
        if GrabSourceType.GOOGLE.value in selected_sources:
            google_grabber = GoogleGrabber()
            google_grabber.full_image = self.image_size == ImageSize.LARGE
            images.extend(google_grabber.get_images_url(self.keyword))

        if GrabSourceType.BING.value in selected_sources:
            bing_grabber = BingGrabber()
            bing_grabber.full_image = self.image_size == ImageSize.LARGE
            images.extend(bing_grabber.get_images_url(self.keyword))

        if ALL_SOURCE in self.sources or len(selected_sources) > 1:
            images = self.__repart_between_image_sources(selected_sources, images)

        nb_urls = len(images)
        if nb_urls == 0:
            print("No image found on sources " + ",".join(list(self.sources)))
        else:
            sub_folder_name = self.__create_destination_folder()
            print("\n %s images found on %s, limit to download set to %s \n" % (nb_urls, self.sources, self.limit))
            self.__download_files(images[:self.limit], sub_folder_name)
            end = time.time()
            print("\n %s images downloaded in %s sec" % (self.limit, end - start))

    def __repart_between_image_sources(self, sources, images):
        nb_by_source = int(math.ceil(self.limit / len(sources)))
        repart_images = []
        for source in sources:
            repart_images.extend([img for img in images if img.source == source][:nb_by_source])
        return repart_images

    def __set_default_file_prefix(self):
        """if no specified file prefix, build one from keyword"""
        if self.file_prefix is None:
            self.file_prefix = StringUtil.underscore_and_lowercase(self.keyword)

    def __create_destination_folder(self):
        """ set default destination to 'images', create and return sub_folder based on keyword name """
        if self.destination is None:
            self.destination = 'images'

        if not os.path.exists(self.destination):
            os.mkdir(self.destination)
        sub_folder = os.path.join(self.destination, StringUtil.underscore_and_lowercase(self.keyword))

        if not os.path.exists(sub_folder):
            os.mkdir(sub_folder)
        return sub_folder

    def __download_files(self, images, folder_name):
        """urls param is a list of GrabbedImage object with url / extension or just base64"""
        for i, image in enumerate(images):
            if i == self.limit:
                break
            try:

                counter = len([i for i in os.listdir(folder_name) if self.file_prefix in i]) + 1
                extension = ".jpg" if image.extension is None else "." + image.extension
                file_name = self.file_prefix + "_" + str(counter) + extension
                f = open(os.path.join(folder_name, file_name), 'wb')

                print("> grabbing %s \n >> saving file %s" % (
                    image.url if image.url else 'from base64 content', file_name)
                )

                if image.base64 is not None:
                    decoded_base64 = base64.decodebytes(bytes(image.base64.split('base64,')[1], 'utf-8'))
                    f.write(decoded_base64)
                elif image.url is not None:
                    raw_img = urllib.request.urlopen(image.url).read()
                    f.write(raw_img)
                f.close()

            except Exception as e:
                print("error while loading/writing image")
                print(e)
                print(image.url if image.url else image.base64[:50])
