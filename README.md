# ProfPair

## Inspiration
We thought of a problem that many students encounter when looking for classes for the upcoming semester. Many new students do not know the "good" or "bad" professors at their university, and the opinion-based reviews on rate my professor might scare off students. To solve this issue we developed a website that uses AI to predict the compatability of students and professors. 

## What it does
The website analyzes student data and their comments using AWS Comprehend to determine the overal score of each professor
Then using Amazon Sage Maker we trained a comprehensive model to determine the compatability of a professor and student based on student input. 

## How we built it
We developed an algorithm using Python to calculate each Professor's score based on their overall rating, difficulty rating, workload rating, all out of five stars, and an overall comment review. Each category was weighed differently to calculate the overall score. To get the specific score from the comment review, we utilized AWS sentiment analysis to calculate the distribution of how positive, negative, neutral, and mixed the comment was. Amazon S3 was used to store these overall scores. The website was developed using HTML and takes in each user's input. A custom-trained model using an AWS Comprehend Model was used to calculate the capability of each professor with the student. 

## Challenges we ran into
One of the hardest parts of the program was creating the data. Because there weren't any reliable data sources for our project. We had to develop our own artificial data to run our program and demonstrate its functionality.

## Accomplishments that we're proud of 
Being able to incorporate AWS technologies into a website to use was one of our biggest accomplishments. Training our own AI model to calculate the compatability between the student and each profesor was also a big accomplsihment. 

## What we learned
Figuring out how to incorporate the AWS services into HTML to display in a local website was one of the things we had to learn in this Hackathon. 

## What's next for ProfPair!
Due to the limited time we had we were not able to add all the functionality to the program. In the future, we would love to add real professors and student reviews for a real representation of what our program can do. Adding more classes, and different universities, and adding a comment feature to the website could be future updates to help improve the program. 
