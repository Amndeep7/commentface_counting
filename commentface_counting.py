import urllib.request
import re
import datetime as dt
from math import log
from pprint import pprint

from pmaw import PushshiftAPI

import matplotlib
matplotlib.set_loglevel("critical")
import matplotlib.pyplot as plt

# url is current as of 2021/11/22
css = urllib.request.urlopen("https://b.thumbs.redditmedia.com/S_eQedWbDdBP2LiQC52C6fleIuSC1sHBZtYlxYMYiew.css").read().decode('utf8')
faces = list(set(re.findall(r'"(#[\w-]+)"', css)).difference(('#s', '#wiki_')))
pprint(faces)

api = PushshiftAPI()

# start_epoch = int(dt.datetime(year=2018, month=7, day=6, tzinfo=dt.timezone.utc).timestamp()) # all cdfs
start_epoch = int(dt.datetime(year=2021, month=12, day=20, hour=5, tzinfo=dt.timezone.utc).timestamp()) # time of writing (2021/12/20)
print('epoch', start_epoch)

cdfs = [cdf['id'] for cdf in api.search_submissions(
    after = start_epoch, # the assumption here is that even through automated means the likelihood of the thread being submitted on/before this time is highly nonexistent
    subreddit = 'anime',
    filter = ['title', 'id'],
    q = 'Casual Discussion' # At some point there was a switch from Friday to Fridays
)]

print("cdfs", cdfs)

# seems like there's a cap on how big the query can be, so this divvies up the query string into acceptable size clumps.
def clump_string(itr, clump_size, sep="||"):
    string = sep.join(itr)
    clumps = []
    while len(string) > clump_size:
        index = clump_size
        while string[index:index + len(sep)] != sep and index >= 0:
            index -= 1
        clumps.append(string[:index])
        string = string[index + len(sep):]
    clumps.append(string)
    return clumps

comments = []
for clump in clump_string(faces, 3000): # seems like 3400 is the max atm, but gonna go with 3000 to be on the safe side
    print(len(clump))
    print(clump)
    comments_clump = [comment for comment in api.search_comments(
        after = start_epoch,
        subreddit = 'anime',
        filter = ['author', 'body', 'link_id'],
        filter_fn = lambda c: c['author'] != 'AutoModerator' and any((face in c['body'] for face in faces)),
        q = clump
    )]
    comments.extend(comments_clump)
comments = [dict(deduped_comment) for deduped_comment in {tuple(comment.items()) for comment in comments}] # dicts are unhashable to can't do the easy `list(set(thing))` trick exactly: https://stackoverflow.com/a/9427216/645647
pprint(comments)

commentators = {face:dict() for face in faces} # TODO: change name of this variable to reflect primary key being faces
for comment in comments:
    for face in faces:
        if face in comment['body']:
            if comment['author'] not in commentators[face]:
                commentators[face][comment['author']] = 0
            commentators[face][comment['author']] += 1
pprint(commentators)

cdf_commentators = set()
for cdf in cdfs:
    cdf_commentators_here = {a['author'] for a in api.search_comments(
        after = start_epoch,
        subreddit = 'anime',
        filter = ['author'],
        link_id = cdf
    )}
    pprint(len(cdf_commentators_here))
    cdf_commentators = cdf_commentators.union(cdf_commentators_here)
pprint(cdf_commentators)

use = dict()
for face in faces:
    total_users = len(commentators[face].keys())
    users_not_in_cdf = len(set(commentators[face].keys()).difference(cdf_commentators))
    total_usages = sum(commentators[face].values())
    usages_not_in_cdf = sum([commentators[face][author] for author in set(commentators[face].keys()).difference(cdf_commentators)])

    percentages = (round(users_not_in_cdf/total_users if total_users != 0 else 0, 5),
                   round(usages_not_in_cdf/total_usages if total_usages != 0 else 0, 5))
    if percentages not in use:
        use[percentages] = 0
    use[percentages] += 1

    print(face, '\ntotal users:', total_users, 'not from cdf:', users_not_in_cdf, '(', round(users_not_in_cdf/total_users, 5) if total_users != 0 else 'n/a', ')\n', 'total usages:', total_usages, 'usages not from cdfers:', usages_not_in_cdf, '(', round(usages_not_in_cdf/total_usages, 5) if total_usages != 0 else 'n/a', ')\n')

use_keys = use.keys()
fig = plt.figure()
ax = fig.add_subplot(111, projection='rectilinear')
pprint(use)
x = [k[0] for k in use_keys]
pprint(x)
y = [k[1] for k in use_keys]
pprint(y)
s = [use[k] for k in use_keys]
pprint(s)
ax.scatter(x, y, [20*2**(log(size)) for size in s], c='r', marker='o')
ax.set_xlabel('Percent of users not in CDF')
ax.set_ylabel('Percent of usages not by CDFers')
plt.savefig('allcdfs.png')
