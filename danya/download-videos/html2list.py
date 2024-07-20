#!/usr/bin/env python

# browse to "videos" page of youtube account
# scroll to bottom (populating the container div)
# use inspector to dump the container's HTML to 'tmp.html'

import re

videos = []

# <a id="video-title-link" class="yt-simple-endpoint focus-on-expand style-scope ytd-rich-grid-media" aria-label="What is a Pillsbury Knight?? | Jobava London | The Sensei Speedrun | GM Naroditsky by Daniel Naroditsky 153,158 views 1 year ago 1 hour, 2 minutes" title="What is a Pillsbury Knight?? | Jobava London | The Sensei Speedrun | GM Naroditsky" href="/watch?v=Ybg_2qbKXdA">

with open('tmp1.html') as fp:
    for line in fp.readlines():
        if m := re.search('<a id="video-title-link".*title="(.*?)" href="(.*?)">', line):
        #if m := re.search('<a id="video-title".*?href="(.*?)">(.*?)</a>', line):
            link = m.group(2)
            title = m.group(1)
            videos.append((f'https://www.youtube.com{link}', title))

for (i, (link, title)) in enumerate(reversed(videos)):
    print(f'{i+1:04d} {link} {title}')

