import datetime as dt
from math import log
import matplotlib.pyplot as plt
from psaw import PushshiftAPI
import re
import urllib.request

# url is current as of 2021/11/22
css = urllib.request.urlopen("https://b.thumbs.redditmedia.com/S_eQedWbDdBP2LiQC52C6fleIuSC1sHBZtYlxYMYiew.css").read().decode('utf8')
faces = set(re.findall(r'"(#[\w-]+)"', css)).difference(('#s', '#wiki_'))

api = PushshiftAPI()

# start_epoch = int(dt.datetime(year=2018, month=7, day=6, tzinfo=dt.timezone.utc).timestamp()) # all cdfs
start_epoch = int(dt.datetime(year=2021, month=11, day=19, tzinfo=dt.timezone.utc).timestamp()) # nov 19 2021 cdf

commentators = dict()
for face in faces:
    print(face)
    authors = [a.author for a in api.search_comments(
        after = start_epoch,
        subreddit = 'anime',
        filter = ['author'],
        q = face
    )]
    print(authors)
    d = dict()
    for a in authors:
        if a not in d:
            d[a] = 0
        d[a] += 1
    print(d)
    commentators[face] = d
print(commentators)

cdfs = [cdf.id for cdf in api.search_submissions(
    after = start_epoch, # the assumption here is that even through automated means the likelihood of the thread being submitted on/before this time is highly nonexistent
    subreddit = 'anime',
    filter = ['title', 'id'],
    q = 'Casual Discussion' # At some point there was a switch from Friday to Fridays
)]

print(cdfs)

cdf_commentators = set()
for cdf in cdfs:
    cdf_commentators_here = {a.author for a in api.search_comments(
        after = start_epoch,
        subreddit = 'anime',
        filter = ['author'],
        link_id = cdf
    )}
    print(len(cdf_commentators_here))
    cdf_commentators = cdf_commentators.union(cdf_commentators_here)
print(cdf_commentators)

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
print(use)
x = [k[0] for k in use_keys]
print(x)
y = [k[1] for k in use_keys]
print(y)
s = [use[k] for k in use_keys]
print(s)
ax.scatter(x, y, [20*2**(log(size)) for size in s], c='r', marker='o')
ax.set_xlabel('Percent of users not in CDF')
ax.set_ylabel('Percent of usages not by CDFers')
plt.savefig('allcdfs.png')
