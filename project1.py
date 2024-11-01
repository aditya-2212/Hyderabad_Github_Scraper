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

import pandas as pd

# Load the users and repositories data
users_df = pd.read_csv('users.csv')
repos_df = pd.read_csv('repositories.csv')

# Ensure 'created_at' columns are in datetime format
users_df['created_at'] = pd.to_datetime(users_df['created_at'])
repos_df['created_at'] = pd.to_datetime(repos_df['created_at'])

# Question 1: Top 5 users in Hyderabad with the highest number of followers
top_5_followers = users_df.nlargest(5, 'followers')['login'].tolist()
print("Top 5 users with highest followers:", top_5_followers)

# Question 2: 5 earliest registered GitHub users in Hyderabad
earliest_users = users_df.nsmallest(5, 'created_at')['login'].tolist()
print("5 earliest registered users:", earliest_users)

# Question 3: Top 3 most popular licenses
top_3_licenses = repos_df['license_name'].value_counts().head(3).index.tolist()
print("Top 3 most popular licenses:", top_3_licenses)

# Question 4: Most common company (after cleaning)
top_company = users_df['company'].mode().iloc[0] if not users_df['company'].mode().empty else None
print("Most common company:", top_company)

# Question 5: Most popular programming language
popular_language = repos_df['language'].mode().iloc[0] if not repos_df['language'].mode().empty else None
print("Most popular programming language:", popular_language)

# Question 6: Second most popular language among users who joined after 2020
recent_users = users_df[users_df['created_at'] >= '2020-01-01']
second_popular_language_recent = recent_users.merge(repos_df, on="login")['language'].value_counts().index[1] if len(recent_users) > 1 else None
print("Second most popular language since 2020:", second_popular_language_recent)

# Question 7: Language with the highest average number of stars per repository
avg_stars_per_language = repos_df.groupby('language')['stargazers_count'].mean().sort_values(ascending=False)
top_language_avg_stars = avg_stars_per_language.idxmax() if not avg_stars_per_language.empty else None
print("Language with highest average stars:", top_language_avg_stars)

# Question 8: Top 5 users by leader_strength = followers / (1 + following)
users_df['leader_strength'] = users_df['followers'] / (1 + users_df['following'])
top_5_leader_strength = users_df.nlargest(5, 'leader_strength')['login'].tolist()
print("Top 5 users by leader strength:", top_5_leader_strength)

# Question 9: Correlation between number of followers and public repositories
correlation_followers_repos = users_df['followers'].corr(users_df['public_repos'])
print("Correlation between followers and public repos:", round(correlation_followers_repos, 3))

# Question 10: Estimate followers gained per additional public repository using regression
from sklearn.linear_model import LinearRegression
import numpy as np

# Fit linear regression model
X = users_df[['public_repos']]
y = users_df['followers']
model = LinearRegression().fit(X, y)
followers_per_repo_slope = model.coef_[0]
print("Followers gained per additional repo:", round(followers_per_repo_slope, 3))

# Question 11: Correlation between projects enabled and wiki enabled
correlation_projects_wiki = repos_df['has_projects'].astype(int).corr(repos_df['has_wiki'].astype(int))
print("Correlation between projects and wiki enabled:", round(correlation_projects_wiki, 3))

# Question 12: Difference in average following between hireable and non-hireable users
hireable_avg_following = users_df[users_df['hireable'] == True]['following'].mean()
non_hireable_avg_following = users_df[users_df['hireable'] == False]['following'].mean()
hireable_following_difference = round(hireable_avg_following - non_hireable_avg_following, 3)
print("Difference in following between hireable and non-hireable users:", hireable_following_difference)

# Question 13: Impact of bio length on followers
users_with_bio = users_df[users_df['bio'].notna()]
users_with_bio['bio_length'] = users_with_bio['bio'].apply(lambda x: len(x.split()))
bio_model = LinearRegression().fit(users_with_bio[['bio_length']], users_with_bio['followers'])
followers_per_bio_word = bio_model.coef_[0]
print("Followers gained per bio word:", round(followers_per_bio_word, 3))

# Question 14: Users with most repositories created on weekends
repos_df['weekday'] = repos_df['created_at'].dt.weekday
weekend_repos = repos_df[repos_df['weekday'] >= 5]  # 5 = Saturday, 6 = Sunday
top_weekend_creators = weekend_repos['login'].value_counts().head(5).index.tolist()
print("Top 5 users creating repos on weekends:", top_weekend_creators)

# Question 15: Fraction difference in email visibility for hireable vs non-hireable users
hireable_with_email = users_df[users_df['hireable'] == True]['email'].notna().mean()
non_hireable_with_email = users_df[users_df['hireable'] == False]['email'].notna().mean()
email_visibility_difference = round(hireable_with_email - non_hireable_with_email, 3)
print("Difference in email visibility (hireable vs non-hireable):", email_visibility_difference)

# Question 16: Most common surname among users (assuming last word in name is surname)
users_df['surname'] = users_df['name'].dropna().apply(lambda x: x.strip().split()[-1] if x else '')
common_surname = users_df['surname'].value_counts().nlargest(1).index.tolist()
print("Most common surname(s):", ', '.join(common_surname))