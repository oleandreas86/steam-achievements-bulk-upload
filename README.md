# Why this python script?
> Uploading/adding/editing achievements in Steam is a pain in the ass and takes forever since you need to edit each entry individually and just adding 1 entry takes more than a handful of clicks. 

> This script automates that using Steam unofficial APIs. This also means that Steam might change their API at some point, which might require this script to be updated.

# Installation & Setup
### Download python 3.13
https://www.python.org/downloads/

### Create your virtual environment
`python3 -m venv venv`

### Activate your virtual environment
`source .venv/bin/activate`

### Install packages
`pip install -r requirements.txt`

### Deactivate your virtual environment
`deactivate`

# How to use this python app
### Find your steam app id
1. Log into Steamworks website, go to the App Admin of your site. 
2. The id says in the header after the name and at the end of the URL, just copy it from there. (i.e. https://partner.steamgames.com/apps/view/YOUR_STEAM_APP_ID)

### Find your cookie information
1. Open the Network tab in your developer console. 
2. Go to the Achievements page.
3. Select one of the entries and scroll down in the details and find the Cookie field. 
4. Copy the content of it into the cookie.txt file.

>This cookie needs to be updated from time to time

### Fill out your achievements data
- Inside ach_data.json you will find all the achievement data that will be uploaded to Steam. This includes the localization data for your achievements.
- There are multiple ways to reach this final list in this format, so here are some examples
    - I have attached an excel file which has an OfficeScript to automatically generate the json. (you will want to sanitize the formatting using https://jsonformatter.curiousconcept.com after copying the output.)
    - You can write the achievements in the json format directly
    - Any other way you can think of :D
- For the images, just add them to the images_dir and write the name of the image file.