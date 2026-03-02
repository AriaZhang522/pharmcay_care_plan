1. Frontend -> API -> Backend

- POST: "Here is new information"Direction: Front-end (with data) $\rightarrow$ API $\rightarrow$ Back-end saves it.


- GET: "Give me information"Direction: Front-end $\rightarrow$ asks API $\rightarrow$ Back-end sends data back.

here user is in the front end. if i want to get info from backend, backend sent info to me -> this is get.

If i want to send info to backend, this is post

## question 4 --- the process is walkthrough, which i should do when interviewing
in the first time, i cannot answer this question.  if i have two api design, but i dn;t have any code, how can i know whether can i use this api.

the answer is : you say the whole process.
firstly i fill the form and click the sumbit button, and the post api start to work, it send my form to backend, waits for 10 sec, the backend say oh, done, the order number is 123 and here is your care plan:

secondly, several days later, i want to see the order whose number is 123, and i call the get api with order number 123, so backend send me the care plan.


my api key: (store in .env locally, do not commit)
name: pharmacy_career_plan



github can detect the real API key in order to avoid revealing

if I change frontend and backend code, i need to rebuild and restart docker to make the new code work.
terminal command line is : `cd /Users/zhangyuyan/Desktop/pharmacy_career_plan/careplan-mvp && docker compose build frontend && docker compose up -d frontend`
