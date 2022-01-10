import csv
import datetime as dt
import re
import urllib.request
from math import log
from pprint import pprint

import matplotlib.pyplot as plt
from pmaw import PushshiftAPI

def get_commentfaces():
    # url is current as of 2021/11/22
    css = urllib.request.urlopen("https://b.thumbs.redditmedia.com/S_eQedWbDdBP2LiQC52C6fleIuSC1sHBZtYlxYMYiew.css").read().decode('utf8')
    faces = list(set(re.findall(r'"(#[\w-]+)"', css)).difference(('#s', '#wiki_')))
    pprint(faces)
    return faces

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

def get_all_comments_using_commentfaces(api, start_epoch, faces):
    comments = []
    for clump in clump_string(faces, 3000): # seems like 3400 is the max atm, but gonna go with 3000 to be on the safe side
        print(len(clump))
        print(clump)
        comments_clump = [comment for comment in api.search_comments(
            after = start_epoch,
            subreddit = 'anime',
            filter = ['author', 'body', 'link_id', 'created_utc'],
            filter_fn = lambda c: c['author'] != 'AutoModerator' and any((face in c['body'] for face in faces)),
            q = clump
        )]
        comments.extend(comments_clump)
    comments = [dict(deduped_comment) for deduped_comment in {tuple(comment.items()) for comment in comments}] # dicts are unhashable to can't do the easy `list(set(thing))` trick exactly: https://stackoverflow.com/a/9427216/645647
    pprint(comments)
    return comments

def get_commentators_by_commentface(faces, comments):
    commentators = {face:dict() for face in faces}
    for comment in comments:
        for face in faces:
            if face in comment['body']:
                if comment['author'] not in commentators[face]:
                    commentators[face][comment['author']] = 0
                commentators[face][comment['author']] += 1
    pprint(commentators)
    return commentators

def get_cdfs(api, start_epoch):
    cdfs = [cdf['id'] for cdf in api.search_submissions(
        after = start_epoch, # the assumption here is that even through automated means the likelihood of the thread being submitted on/before this time is highly nonexistent
        subreddit = 'anime',
        filter = ['title', 'id'],
        q = 'Casual Discussion' # At some point there was a switch from Friday to Fridays
    )]
    print("cdfs", cdfs)
    return cdfs

# todo: options to modify this to do things like check if participated in multiple cdfs, dumped more than one comment, and/or if a certain percentage of /r/anime comments are in cdf so as to better claim these commentators as being cdfers
def get_cdf_commentators(api, start_epoch, cdfs):
    cdf_commentators = set()
    for cdf in cdfs:
        cdf_commentators_here = {a['author'] for a in api.search_comments(
            after = start_epoch,
            subreddit = 'anime',
            filter = ['author'],
            link_id = cdf
        )}
        pprint(len(cdf_commentators_here))
        cdf_commentators = cdf_commentators.union(cdf_commentators_here) # todo: do the union outside the loop
    pprint(cdf_commentators)
    return cdf_commentators

def analysis_and_visualization(faces, commentators, cdf_commentators):
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

def commentators_by_commentfaces_csv(commentators, cdf_commentators, faces):
    headers = ['User', 'CDFer'] + sorted(faces)
    
    reverse_face_data = {}
    for face in faces:
        for commentator, count in commentators[face].items():
            if commentator not in reverse_face_data:
                reverse_face_data[commentator] = {f: 0 for f in faces}
            reverse_face_data[commentator][face] = count
    pprint(reverse_face_data)

    data = [{'User': commentator, 'CDFer': commentator in cdf_commentators} | face_data  for commentator, face_data in sorted(reverse_face_data.items())]

    with open('all_commentators_by_commentface.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, headers)
        writer.writeheader()
        writer.writerows(data)

def main():
    faces = get_commentfaces()

    api = PushshiftAPI()

    # start_epoch = int(dt.datetime(year=2018, month=7, day=6, tzinfo=dt.timezone.utc).timestamp()) # all cdfs
    start_epoch = int(dt.datetime(year=2022, month=1, day=7, tzinfo=dt.timezone.utc).timestamp()) # most recent cdf as of time of writing (2022/1/7)
    print('epoch', start_epoch)

    comments = get_all_comments_using_commentfaces(api, start_epoch, faces)
    commentators = get_commentators_by_commentface(faces, comments)

    cdfs = get_cdfs(api, start_epoch)
    cdf_commentators = get_cdf_commentators(api, start_epoch, cdfs)

    analysis_and_visualization(faces, commentators, cdf_commentators)
    commentators_by_commentfaces_csv(commentators, cdf_commentators, faces)

if __name__ == "__main__":
    main()
