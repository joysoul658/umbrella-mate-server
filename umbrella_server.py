from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import random

system_state = {
    "auth_count": 0,
    "command": "none",
    "authenticated_users": [],
    "current_pin": f"{random.randint(100000, 999999)}",
    "hardware_status": "locked",
    "umbrella_left": 7,
    "is_raining": False,
    "display_message": "디스플레이 PIN 번호를 확인하세요"
}

HTML_PAGE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>우산메이트 - Umbrella Mate</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8f9fa; margin: 0; padding-bottom: 80px; }
        
        #login-screen { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: #f8f9fa; z-index: 2000; display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 20px; }
        .login-card { background: white; width: 100%; max-width: 360px; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); text-align: center; }
        .login-input { width: 100%; padding: 14px; margin: 10px 0; border: 1px solid #ddd; border-radius: 10px; font-size: 15px; outline: none; }
        .login-btn { width: 100%; background: #007bff; color: white; border: none; padding: 14px; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 10px; }

        #app-screen { display: none; }
        .header { padding: 20px 20px 10px 20px; }
        .weather-notice { font-size: 13px; color: #555; margin-bottom: 5px; font-weight: bold; }
        .title { font-size: 22px; font-weight: bold; color: #111; line-height: 1.3; }
        
        .umbrella-card { background: linear-gradient(135deg, #0072ff 0%, #00c6ff 100%); color: white; margin: 15px 20px; padding: 20px; border-radius: 20px; box-shadow: 0 4px 15px rgba(0, 114, 255, 0.3); position: relative; }
        .umbrella-location { font-size: 13px; opacity: 0.9; margin-bottom: 8px; }
        .umbrella-count { font-size: 26px; font-weight: bold; margin-bottom: 12px; }
        .lock-badge { position: absolute; top: 20px; right: 20px; background: rgba(255, 255, 255, 0.2); padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; transition: all 0.3s; }

        .hardware-monitor { background: white; margin: 15px 20px; padding: 15px 20px; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); font-size: 13px; color: #441; line-height: 1.6; }
        .hardware-monitor h4 { margin: 0 0 8px 0; font-size: 14px; color: #0056b3; }

        .filter-container { display: flex; gap: 8px; overflow-x: auto; padding: 0 20px 15px 20px; white-space: nowrap; }
        .chip { background: white; border: 1px solid #ddd; padding: 8px 14px; border-radius: 20px; font-size: 13px; color: #333; cursor: pointer; }
        .chip.active { background: #0056b3; color: white; border-color: #0056b3; font-weight: bold; }
        
        .mate-card { background: white; margin: 10px 20px; padding: 15px 20px; border-radius: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); display: flex; justify-content: space-between; align-items: center; }
        .mate-info h4 { margin: 0 0 5px 0; font-size: 16px; color: #333; }
        .mate-info p { margin: 0; font-size: 12px; color: #666; }
        .chat-go-btn { background: #e7f1ff; color: #0056b3; border: none; padding: 8px 14px; border-radius: 8px; font-size: 13px; font-weight: bold; cursor: pointer; }

        .pin-container { background: #f1f3f5; padding: 20px; border-radius: 15px; margin-top: 15px; text-align: center; }
        .pin-notice { font-size: 13px; color: #d9534f; font-weight: bold; margin-bottom: 10px; background: #fff3f3; padding: 8px; border-radius: 8px; }
        .pin-input { width: 100%; padding: 14px; font-size: 22px; text-align: center; letter-spacing: 6px; border: 1px solid #ddd; border-radius: 10px; margin-top: 5px; outline: none; background: white; color: #111; }
        .auth-btn { background: #0056b3; color: white; border: none; padding: 14px 20px; font-size: 15px; border-radius: 10px; cursor: pointer; margin-top: 10px; width: 100%; font-weight: bold; }

        .content-section { margin: 20px; background: white; padding: 25px 20px; border-radius: 20px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.03); }
        .tab-bar { position: fixed; bottom: 0; left: 0; right: 0; height: 65px; background: white; border-top: 1px solid #eee; display: flex; justify-content: space-around; align-items: center; z-index: 1000; }
        .tab-item { text-align: center; font-size: 11px; color: #888; cursor: pointer; flex: 1; }
        .tab-item.active { color: #0056b3; font-weight: bold; }
        .tab-item div:first-child { font-size: 20px; margin-bottom: 2px; }
    </style>
    <script>
        let loggedInUser = ""; let loggedInDept = ""; let loggedInRoute = ""; let currentFilter = "전체";
        
        // 숭실대학교 캠퍼스 건물 및 동선 기반 메이트 더미 데이터
        const matesData = [
            { id: 1, name: "김민수", route: "숭실대입구역 ➔ 형남공학관", hasUmbrella: true, gender: "남성" },
            { id: 2, name: "이지원", route: "정문 ➔ 조만식기념관", hasUmbrella: true, gender: "여성" },
            { id: 3, name: "박준영", route: "기숙사 ➔ 학생회관", hasUmbrella: false, gender: "남성" }
        ];

        function handleLogin(event) {
            event.preventDefault();
            loggedInUser = document.getElementById('username-input').value.trim();
            if (!loggedInUser) { alert("이름을 입력해주세요!"); return; }
            loggedInDept = document.getElementById('dept-input').value.trim() || "정보사회학과";
            loggedInRoute = document.getElementById('route-input').value.trim() || "숭실대입구역 ➔ 조만식기념관";

            document.getElementById('login-screen').style.display = 'none';
            document.getElementById('app-screen').style.display = 'block';
            document.getElementById('greeting-title').innerText = `${loggedInUser}님, 메이트를 찾아볼까요?`;
            switchTab('matching');
        }

        function switchTab(tabName) {
            document.querySelectorAll('.tab-item').forEach(el => el.classList.remove('active'));
            document.getElementById('tab-' + tabName).classList.add('active');
            const mainContent = document.getElementById('main-content');

            if (tabName === 'matching') {
                renderMatchingTab();
            } else if (tabName === 'qr') {
                mainContent.innerHTML = `
                    <div class="content-section" style="margin-top:20px;">
                        <h3 style="margin-bottom:5px;">🔑 2인 일회용 PIN 인증</h3>
                        <p style="font-size:13px; color:#666;">우산함 앞 아두이노 디스플레이에 표시된 6자리 숫자를 확인하세요.</p>
                        
                        <div class="pin-container">
                            <div class="pin-notice">⚠️ PIN 번호는 우산함 디스플레이에서만 볼 수 있습니다.</div>
                            <input type="text" id="pin-input-field" class="pin-input" maxlength="6" placeholder="------">
                            <button class="auth-btn" id="submit-auth-btn">🔓 인증하기</button>
                        </div>

                        <div style="margin-top:15px; font-weight:bold; color:#333; font-size:14px;" id="auth-status-text">인증 인원: 확인 중...</div>
                    </div>
                `;
                setTimeout(() => {
                    const btn = document.getElementById('submit-auth-btn');
                    if (btn) {
                        btn.onclick = submitPinAuth;
                    }
                }, 100);
            } else if (tabName === 'profile') {
                mainContent.innerHTML = `<div class="content-section" style="margin-top:20px;"><h3>👤 ${loggedInUser}님의 프로필</h3><p style="font-size:14px; color:#555; margin-top:10px;">소속: ${loggedInDept}</p><p style="font-size:14px; color:#555;">이동 경로: ${loggedInRoute}</p></div>`;
            } else if (tabName === 'chat') {
                mainContent.innerHTML = `<div class="content-section" style="margin-top:40px;"><h3>💬 채팅</h3><p style="font-size:14px; color:#666;">준비 중인 기능입니다.</p></div>`;
            }
        }

        function renderMatchingTab() {
            let filtered = matesData;
            if (currentFilter === '우산 있는 사람만') filtered = matesData.filter(m => m.hasUmbrella);
            else if (currentFilter === '내 동선과 겹침') filtered = matesData.filter(m => m.route.includes("숭실대입구역") || m.route.includes("조만식기념관"));
            
            let matesHtml = filtered.length === 0 ? `<div class="content-section"><div style="color:#666; font-size:14px;">조건에 맞는 메이트가 없어요</div></div>` : filtered.map(m => `
                <div class="mate-card">
                    <div class="mate-info"><h4>${m.name} (${m.gender}) ${m.hasUmbrella ? '☂️ 우산 보유' : ''}</h4><p>📍 ${m.route}</p></div>
                    <button class="chat-go-btn" onclick="alert('채팅 기능 준비중입니다.')">채팅하기</button>
                </div>`).join('');

            document.getElementById('main-content').innerHTML = `
                <div class="umbrella-card">
                    <div class="lock-badge" id="lock-status">상태 확인 중...</div>
                    <div class="umbrella-location">우산함 1호 · 조만식기념관 1층 로비</div>
                    <div class="umbrella-count" id="umbrella-count-display">-- / 10개 남음</div>
                </div>
                
                <div class="hardware-monitor">
                    <h4>🛠️ 하드웨어 센서 연동 상태</h4>
                    <div>• 🌧️ 빗물감지센서: <span id="rain-status-text" style="font-weight:bold;">확인 중...</span></div>
                    <div>• 🖥️ 아두이노 디스플레이: <span id="display-msg-text" style="font-weight:bold; color:#0056b3;">-</span></div>
                </div>

                <div class="filter-container">
                    <div class="chip ${currentFilter === '전체' ? 'active' : ''}" onclick="currentFilter='전체'; renderMatchingTab();">전체</div>
                    <div class="chip ${currentFilter === '우산 있는 사람만' ? 'active' : ''}" onclick="currentFilter='우산 있는 사람만'; renderMatchingTab();">☂️ 우산 보유</div>
                    <div class="chip ${currentFilter === '내 동선과 겹침' ? 'active' : ''}" onclick="currentFilter='내 동선과 겹침'; renderMatchingTab();">📍 동선 일치</div>
                </div>
                <div>${matesHtml}</div>
            `;
        }

        async function submitPinAuth() {
            const inputField = document.getElementById('pin-input-field');
            if (!inputField) {
                alert("입력창을 찾을 수 없습니다.");
                return;
            }
            const enteredPin = inputField.value.trim();
            if (!enteredPin || enteredPin.length !== 6) {
                alert("6자리 PIN 번호를 정확히 입력해주세요!");
                return;
            }

            try {
                const res = await fetch('/api/auth', { 
                    method: 'POST', 
                    headers: { 'Content-Type': 'application/json' }, 
                    body: JSON.stringify({ user: loggedInUser, pin: enteredPin }) 
                });
                const data = await res.json();
                alert(data.message);
                inputField.value = '';
            } catch (e) {
                alert("서버 통신 중 에러가 발생했습니다.");
            }
        }

        setInterval(async () => {
            try {
                const res = await fetch('/api/state');
                const data = await res.json();
                
                const countDisplay = document.getElementById('umbrella-count-display');
                if (countDisplay) countDisplay.innerText = `${data.umbrella_left} / 10개 남음`;

                const rainNotice = document.getElementById('rain-notice-text');
                const rainStatus = document.getElementById('rain-status-text');
                if (data.is_raining) {
                    if (rainNotice) rainNotice.innerText = "🌧️ 현재 비가 내리고 있습니다! 우산 메이트를 찾아보세요";
                    if (rainStatus) { rainStatus.innerText = "비 감지됨 (강수 중)"; rainStatus.style.color = "#d9534f"; }
                } else {
                    if (rainNotice) rainNotice.innerText = "☀️ 현재 맑음 / 비 소식 없음";
                    if (rainStatus) { rainStatus.innerText = "비 감지 안 됨 (맑음)"; rainStatus.style.color = "#5cb85c"; }
                }

                const displayMsg = document.getElementById('display-msg-text');
                if (displayMsg) displayMsg.innerText = `"${data.display_message}"`;

                const lockBadge = document.getElementById('lock-status');
                if (lockBadge) {
                    if (data.command === 'open') {
                        lockBadge.innerText = '🔓 문 열리는 중';
                        lockBadge.style.background = 'rgba(255, 215, 0, 0.4)';
                    } else if (data.hardware_status === 'unlocked') {
                        lockBadge.innerText = '🔓 도어락 개방됨';
                        lockBadge.style.background = 'rgba(40, 167, 69, 0.8)';
                    } else {
                        lockBadge.innerText = '🔒 도어락 잠김';
                        lockBadge.style.background = 'rgba(255, 255, 255, 0.2)';
                    }
                }

                const statusEl = document.getElementById('auth-status-text');
                if (statusEl) statusEl.innerText = `현재 인증 인원: ${data.auth_count} / 2명 (${data.authenticated_users.join(', ') || '없음'})`;
            } catch(e) {}
        }, 1000);
    </script>
</head>
<body>
    <div id="login-screen">
        <div class="login-card">
            <h2>☂️ 우산메이트 앱</h2>
            <p style="font-size:13px; color:#666; margin-bottom:20px;">시연용 사용자 정보를 입력해주세요</p>
            <form onsubmit="handleLogin(event)">
                <input type="text" id="username-input" class="login-input" placeholder="이름 (예: 전이솔)" required>
                <input type="text" id="dept-input" class="login-input" placeholder="학과 (예: 산업정보시스템공학과)">
                <input type="text" id="route-input" class="login-input" placeholder="이동 경로 (예: 숭실대입구역 ➔ 조만식기념관)">
                <button type="submit" class="login-btn">앱 시작하기</button>
            </form>
        </div>
    </div>
    <div id="app-screen">
        <div class="header">
            <div class="weather-notice" id="rain-notice-text">☂️ 날씨 센서 확인 중...</div>
            <div class="title" id="greeting-title"></div>
        </div>
        <div id="main-content"></div>
        <div class="tab-bar">
            <a class="tab-item active" id="tab-matching" onclick="switchTab('matching')"><div>🏠</div>매칭</a>
            <a class="tab-item" id="tab-chat" onclick="switchTab('chat')"><div>💬</div>채팅</a>
            <a class="tab-item" id="tab-qr" onclick="switchTab('qr')"><div>🔑</div>PIN 인증</a>
            <a class="tab-item" id="tab-profile" onclick="switchTab('profile')"><div>👤</div>내 정보</a>
        </div>
    </div>
</body>
</html>"""

class AppServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global system_state
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            safe_state = system_state.copy()
            safe_state.pop("current_pin", None) 
            self.wfile.write(json.dumps(safe_state).encode('utf-8'))
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            print(f">>> [디스플레이 동기화] 현재 아두이노 디스플레이 PIN 번호: [{system_state['current_pin']}]")
            response_data = {
                "command": system_state["command"],
                "current_pin": system_state["current_pin"]
            }
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
            if system_state["command"] == "open":
                print(">>> [하드웨어 연동] 아두이노가 도어락 개방(open) 명령을 수신했습니다!")
                system_state["command"] = "none"
                system_state["auth_count"] = 0
                system_state["authenticated_users"] = []
                system_state["current_pin"] = f"{random.randint(100000, 999999)}"
                print(f">>> [PIN 갱신] 새로운 6자리 PIN 번호가 발급되었습니다: [{system_state['current_pin']}]")
                system_state["display_message"] = "도어락 개방 완료 / PIN 갱신됨"
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global system_state
        if self.path == '/api/auth':
            content_length = int(self.headers['Content-Length'])
            req_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            username = req_data.get("user", "사용자")
            entered_pin = req_data.get("pin", "")

            print(f">>> [인증 요청] 사용자: {username} / 입력한 PIN: {entered_pin} / 실제 PIN: {system_state['current_pin']}")

            if entered_pin != system_state["current_pin"]:
                msg = f"❌ 디스플레이에 표시된 6자리 PIN 번호가 일치하지 않습니다!"
            elif username in system_state["authenticated_users"]:
                msg = f"⚠️ {username}님은 이미 PIN 인증을 완료하셨습니다!"
            else:
                system_state["authenticated_users"].append(username)
                system_state["auth_count"] = len(system_state["authenticated_users"])

                if system_state["auth_count"] >= 2:
                    system_state["command"] = "open"
                    system_state["display_message"] = "2인 PIN 인증 완료! 문이 열립니다"
                    msg = f"🎉 2인 PIN 인증 완료! 솔레노이드 도어락 개방 신호를 보냅니다."
                else:
                    system_state["display_message"] = f"1명 인증 완료 ({system_state['auth_count']}/2)"
                    msg = f"✅ {username}님 1차 PIN 인증 완료! (현재 {system_state['auth_count']}/2명). 동행자의 인증이 필요합니다."

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"message": msg}).encode('utf-8'))
        elif self.path == '/api/report':
            content_length = int(self.headers['Content-Length'])
            req_data = json.loads(self.rfile.read(content_length).decode('utf-8'))
            
            if "status" in req_data:
                system_state["hardware_status"] = req_data["status"]
            if "umbrella_left" in req_data:
                system_state["umbrella_left"] = req_data["umbrella_left"]
            if "is_raining" in req_data:
                system_state["is_raining"] = req_data["is_raining"]
            if "display_message" in req_data:
                system_state["display_message"] = req_data["display_message"]
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"result": "success"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server_address = ('0.0.0.0', 5001)
    httpd = HTTPServer(server_address, AppServerHandler)
    print("==================================================")
    print(" ☂️ 숭실대 캠퍼스 버전 우산메이트 서버 시작")
    print(f" 🔑 초기 발급된 PIN 번호: [{system_state['current_pin']}]")
    print("==================================================")
    httpd.serve_forever()
