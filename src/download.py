import gdown

url = 'https://drive.google.com/uc?export=download&id=1O4wzIwWgTmc9Xgt5dgrg6ctH68AoKcTJ'
output = '../autoblox_traces.zip'
gdown.download(url, output, quiet=False)

url = 'https://drive.google.com/uc?export=download&id=1ha25yZPiIT2U_9i3tI9w9uL5oM3fsKbE'
output = '../xdb_base.zip'
gdown.download(url, output, quiet=False)