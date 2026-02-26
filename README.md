# Sportsbook Arbitrage Engine

> This repo stores the backend for deployment of the arbitrage engine.

---

## 📌 Overview

One common issue among just about every person who indulges themselves with gambling is **losing**. 
What if there was a way to gaurantee that a player can always beat the sportsbook? That is where 
Arbitrage betting comes in, and serves as a way to gaurantee profit and abuse poorly places lines
within the market. This engine runs the behind the scenes work that processes sportsbook API data
to identify these spots of gauranteed profit, and upload them to a database where my own live API
lives. See the frontend repository [here](https://github.com/cspannuth/Arbitrage_Frontend) that
incorporates it!

---

## 🚀 Features

- Live upon demand fetching of arbitrage opportunities in real sportsbook markets
- Processes the data received and formats into database ready tables
- Features automatic table insertion upon detection
- Hosts a live API for the front-end to access
- Encrypted JWT authentication tokens for data fetching
- Support for various types of bets and markets

---

## 🛠 Tech Stack

**Languages**
- Python

**Backend**
- FastAPI
- Render
- Docker 

**Database**
- PostgreSQL (Supabase)

---

## 🏗 Architecture

Describe:
- Separated into a scalabale file structure
- Every function in the backend is currently meant
  to call itself for the user to make a simple
  authenticated call to the API
- Further segmentation is in progress, and will be needed
  upon the addition of new features.
  
## 👤 Author

William Spannuth 
LinkedIn: www.linkedin.com/in/connorspannuth
