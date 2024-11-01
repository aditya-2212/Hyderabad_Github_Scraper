# -*- coding: utf-8 -*-
"""Project1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1mPZ28-F_V0TrbrUQOH4DldtzZ40Ci_9u
"""

!pip install requests pandas
import requests
import pandas as pd
from datetime import datetime
from statistics import mean
import re

token = "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"
headers = {'Authorization': f'token {token}'}

base_url = "https://api.github.com"

def fetch_users_in_hyderabad(min_followers=50):
    users_data = []
    page = 1
    while True:
        url = f"{base_url}/search/users?q=location:Hyderabad+followers:>{min_followers}&page={page}&per_page=100"
        response = requests.get(url, headers=headers)
        data = response.json().get("items", [])

        if not data:
            break

        for user in data:
            user_info = requests.get(user['url'], headers=headers).json()
            users_data.append({
                "login": user_info['login'],
                "name": user_info.get('name', ''),
                "company": clean_company(user_info.get('company', '')),
                "location": user_info.get('location', ''),
                "email": user_info.get('email', ''),
                "hireable": user_info.get('hireable', ''),
                "bio": user_info.get('bio', ''),
                "public_repos": user_info.get('public_repos', 0),
                "followers": user_info.get('followers', 0),
                "following": user_info.get('following', 0),
                "created_at": user_info.get('created_at', '')
            })
        page += 1
    return pd.DataFrame(users_data)

def clean_company(company):
    if company:
        company = company.strip()
        if company.startswith('@'):
            company = company[1:]
        company = company.upper()
    return company

users_df = fetch_users_in_hyderabad()
users_df.to_csv('users.csv', index=False)

def fetch_repositories_for_users(users_df):
    repos_data = []
    for login in users_df['login']:
        page = 1
        while True:
            url = f"{base_url}/users/{login}/repos?page={page}&per_page=100"
            response = requests.get(url, headers=headers)
            repos = response.json()

            if not repos:
                break

            for repo in repos:
                license_name = repo['license']['key'] if repo.get('license') else ''

                repos_data.append({
                    "login": login,
                    "full_name": repo['full_name'],
                    "created_at": repo['created_at'],
                    "stargazers_count": repo['stargazers_count'],
                    "watchers_count": repo['watchers_count'],
                    "language": repo.get('language', ''),
                    "has_projects": repo.get('has_projects', False),
                    "has_wiki": repo.get('has_wiki', False),
                    "license_name": license_name
                })
            page += 1
    return pd.DataFrame(repos_data)

repos_df = fetch_repositories_for_users(users_df)
repos_df.to_csv('repositories.csv', index=False)

from scipy import stats
import pandas as pd

def analyze_data(users_df, repos_df):
    results = {}

    # 1. Top 5 users by followers
    results['top_followers'] = users_df.nlargest(5, 'followers')['login'].tolist()

    # 2. 5 earliest users
    results['earliest_users'] = users_df.sort_values('created_at').head(5)['login'].tolist()

    # 3. Top 3 licenses (ignoring empty values)
    results['top_licenses'] = repos_df[repos_df['license_name'] != '']['license_name'].value_counts().head(3).index.tolist()

    # 4. Most common company
    results['top_company'] = users_df[users_df['company'] != '']['company'].mode().iloc[0]

    # 5. Most popular language
    results['top_language'] = repos_df['language'].mode().iloc[0]

    # 6. Second most popular language for users after 2020
    users_2020 = users_df[pd.to_datetime(users_df['created_at']).dt.year > 2020]['login']
    recent_repos = repos_df[repos_df['login'].isin(users_2020)]
    results['second_language_2020'] = recent_repos['language'].value_counts().index[1]

    # 7. Language with highest average stars
    avg_stars = repos_df.groupby('language')['stargazers_count'].mean()
    results['highest_stars_language'] = avg_stars.idxmax()

    # 8. Top 5 by leader strength
    users_df['leader_strength'] = users_df['followers'] / (1 + users_df['following'])
    results['top_leaders'] = users_df.nlargest(5, 'leader_strength')['login'].tolist()

    # 9. Correlation followers vs repos
    results['follower_repo_corr'] = round(users_df['followers'].corr(users_df['public_repos']), 3)

    # 10. Regression slope followers vs repos
    slope, _, _, _, _ = stats.linregress(users_df['public_repos'], users_df['followers'])
    results['follower_repo_slope'] = round(slope, 3)

    # 11. Projects and wiki correlation (ensure NaN handled as False)
    repos_df['has_projects'] = repos_df['has_projects'].fillna(False).astype(int)
    repos_df['has_wiki'] = repos_df['has_wiki'].fillna(False).astype(int)
    results['projects_wiki_corr'] = round(repos_df['has_projects'].corr(repos_df['has_wiki']), 3)

    # 12. Hireable following difference
    users_df['hireable'] = users_df['hireable'].fillna(False)
    hireable_following = users_df[users_df['hireable'] == True]['following'].mean()
    non_hireable_following = users_df[users_df['hireable'] == False]['following'].mean()
    results['hireable_following_diff'] = round(hireable_following - non_hireable_following, 3)

    # 13. Bio length impact on followers
    users_with_bio = users_df[users_df['bio'].notna() & (users_df['bio'] != '')]
    users_with_bio['bio_words'] = users_with_bio['bio'].str.split().str.len()
    slope, _, _, _, _ = stats.linregress(users_with_bio['bio_words'], users_with_bio['followers'])
    results['bio_impact'] = round(slope, 3)

    # 14. Weekend warriors
    repos_df['created_day'] = pd.to_datetime(repos_df['created_at']).dt.dayofweek
    weekend_repos = repos_df[repos_df['created_day'].isin([5, 6])].groupby('login').size()
    results['weekend_warriors'] = weekend_repos.nlargest(5).index.tolist()

    # 15. Hireable email sharing difference
    hireable_email_fraction = users_df[users_df['hireable'] == True]['email'].notna().mean()
    non_hireable_email_fraction = users_df[users_df['hireable'] == False]['email'].notna().mean()
    results['hireable_email_diff'] = round(hireable_email_fraction - non_hireable_email_fraction, 3)

    # 16. Most common surname
    users_df['surname'] = users_df['name'].fillna('').str.strip().str.split().str[-1]
    results['common_surnames'] = users_df[users_df['surname'] != '']['surname'].mode().sort_values().tolist()

    return results

# Analyze data
results = analyze_data(users_df, repos_df)

# Print results
print("\nResults:")
print("1. Top 5 users by followers:", ",".join(results['top_followers']))
print("2. 5 earliest users:", ",".join(results['earliest_users']))
print("3. Top 3 licenses:", ",".join(results['top_licenses']))
print("4. Most common company:", results['top_company'])
print("5. Most popular language:", results['top_language'])
print("6. Second most popular language (post-2020):", results['second_language_2020'])
print("7. Language with highest average stars:", results['highest_stars_language'])
print("8. Top 5 by leader strength:", ",".join(results['top_leaders']))
print("9. Followers-repos correlation:", results['follower_repo_corr'])
print("10. Followers-repos slope:", results['follower_repo_slope'])
print("11. Projects-wiki correlation:", results['projects_wiki_corr'])
print("12. Hireable following difference:", results['hireable_following_diff'])
print("13. Bio length impact:", results['bio_impact'])
print("14. Weekend warriors:", ",".join(results['weekend_warriors']))
print("15. Hireable email difference:", results['hireable_email_diff'])
print("16. Most common surnames:", ",".join(results['common_surnames']))