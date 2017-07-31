# # -*- coding:utf-8 -*-


from distutils.core import setup  
  
PACKAGE = "yueban"  
NAME = "yueban"  
DESCRIPTION = "This is a simple distributed game server"  
AUTHOR = "Yangbo"  
AUTHOR_EMAIL = "yangbo1024@qq.com"  
URL = "https://github.com/yangbo1024/yueban_server"  
VERSION = __import__(PACKAGE).__version__  
  
setup(  
    name=NAME,  
    version=VERSION,  
    description=DESCRIPTION,  
    # long_description=read("README.md"),  
    author=AUTHOR,  
    author_email=AUTHOR_EMAIL,  
    license="FREE",  
    url=URL,  
    packages=["yueban"],  
    classifiers=[  
        "Development Status :: 0.9",  
        "Environment :: Web Environment",  
        "Intended Audience :: Developers",  
        "Operating System :: OS Independent",  
        "Programming Language :: Python",  
    ],  
)  
