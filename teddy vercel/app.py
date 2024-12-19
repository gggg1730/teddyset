from flask import Flask, render_template_string, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

# MongoDB Atlas 연결 설정
MONGO_URI = "mongodb+srv://gggg1730:Wodbs0503!@cluster0.ouzg0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["seats_db"]
seats_collection = db["seats"]

# 초기 데이터 설정
def initialize_seats():
    if seats_collection.count_documents({}) == 0:  # 좌석 데이터가 없는 경우
        for row in "ABCDEFGH":
            for col in range(12):
                seat_id = f"{row}{col}"
                seats_collection.insert_one({"seat_id": seat_id, "student_id": None})

initialize_seats()

# HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>좌석 선택 시스템</title>
  <style>
    body { font-family: Arial, sans-serif; text-align: center; }
    input { margin: 10px; padding: 10px; }
    button { padding: 10px; cursor: pointer; }
    .seat-grid {
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 5px;
      justify-items: center;
      max-width: 600px;
      margin: auto;
    }
    .seat {
      width: 40px; height: 40px; background-color: lightblue;
      border: 1px solid #333; cursor: pointer; text-align: center;
    }
    .seat.sold { background-color: gray; cursor: not-allowed; }
  </style>
</head>
<body>
  <h1 id="welcome">환영합니다!</h1>
  <div id="login-screen">
    <h2>로그인</h2>
    <input type="text" id="studentId" placeholder="학번 입력 (예: 2414)" maxlength="4">
    <button onclick="login()">로그인</button>
  </div>

  <div id="seat-selection" style="display:none;">
    <h2>좌석 선택</h2>
    <div class="seat-grid" id="seatGrid"></div>
  </div>

  <script>
    let studentId = null;
    let seats = {};

    async function loadSeats() {
      const response = await fetch("/seats");
      seats = await response.json();
      renderSeats();
    }

    function login() {
      studentId = document.getElementById('studentId').value;
      if (studentId.length === 4) {
        document.getElementById('welcome').innerText = `${studentId}님, 환영합니다!`;
        document.getElementById('login-screen').style.display = 'none';
        document.getElementById('seat-selection').style.display = 'block';
        loadSeats();
      } else {
        alert("학번을 정확히 입력해주세요.");
      }
    }

    function renderSeats() {
      const seatGrid = document.getElementById('seatGrid');
      seatGrid.innerHTML = '';
      for (let row of "ABCDEFGH") {
        for (let col = 0; col < 12; col++) {
          const seatId = `${row}${col}`;
          const seatDiv = document.createElement('div');
          seatDiv.classList.add('seat');
          if (seats[seatId]) seatDiv.classList.add('sold');
          seatDiv.innerText = seatId;
          seatDiv.onclick = () => selectSeat(seatId);
          seatGrid.appendChild(seatDiv);
        }
      }
    }

    async function selectSeat(seatId) {
      if (seats[seatId]) {
        alert("이미 선택된 좌석입니다.");
        return;
      }
      const response = await fetch("/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seatId, studentId })
      });
      const result = await response.json();
      if (response.ok) {
        alert(result.message);
        loadSeats();
      } else {
        alert(result.message);
      }
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/seats", methods=["GET"])
def get_seats():
    # MongoDB에서 좌석 데이터를 조회
    seats = {seat["seat_id"]: seat["student_id"] for seat in seats_collection.find()}
    return jsonify(seats)

@app.route("/select", methods=["POST"])
def select_seat():
    data = request.get_json()
    seat_id = data.get("seatId")
    student_id = data.get("studentId")

    # 이미 좌석을 선택한 학생인지 확인
    if seats_collection.find_one({"student_id": student_id}):
        return jsonify({"status": "error", "message": "이미 좌석을 선택하셨습니다."}), 400

    # 좌석이 이미 선택되었는지 확인
    if seats_collection.find_one({"seat_id": seat_id, "student_id": {"$ne": None}}):
        return jsonify({"status": "error", "message": "이미 선택된 좌석입니다."}), 400

    # 좌석 선택
    seats_collection.update_one({"seat_id": seat_id}, {"$set": {"student_id": student_id}})
    return jsonify({"status": "success", "message": "좌석이 선택되었습니다."})

