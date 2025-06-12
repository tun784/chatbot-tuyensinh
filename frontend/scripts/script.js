document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("questionInput");
  const sendBtn = document.getElementById("sendButton");
  const chatBox = document.getElementById("chat-box");

  function appendMessage(sender, message, audioUrl = null) {
    const div = document.createElement("div");
    div.classList.add(sender === "user" ? "user-msg" : "bot-msg");

    const strong = document.createElement("strong");
    strong.textContent = sender === "user" ? "" : "";
    div.appendChild(strong);

    const span = document.createElement("span");
    div.appendChild(span);
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (sender === "user") {
      span.textContent = message;
    } else {
      let i = 0;
      const speed = 10; // Độ trễ giữa các ký tự (ms)
      const typeWriter = () => {
        if (i < message.length) {
          span.textContent += message.charAt(i);
          i++;
          chatBox.scrollTop = chatBox.scrollHeight;
          setTimeout(typeWriter, speed);
        } else {
          // Sau khi hiện xong text, thêm nút phát âm thanh nếu có audioUrl
          if (audioUrl) {
            // Nút play
            const playBtn = document.createElement("button");
            playBtn.className = "play-btn-img";
            playBtn.title = "Phát âm thanh";
            playBtn.style.background = "none";
            playBtn.style.border = "none";
            playBtn.style.outline = "none";
            playBtn.style.cursor = "pointer";
            playBtn.style.marginTop = "6px";
            playBtn.style.marginLeft = "0";
            playBtn.style.display = "inline-flex";
            playBtn.style.alignItems = "center";
            playBtn.style.justifyContent = "center";
            playBtn.style.width = "32px";
            playBtn.style.height = "32px";
            playBtn.style.padding = "0";
            playBtn.innerHTML = `<img src='img/play.svg' alt='Play' style='width:28px;height:28px;transition:filter 0.2s;'>`;
            playBtn.onmouseover = () => {
              playBtn.querySelector("img").style.filter =
                "brightness(0.7) drop-shadow(0 0 4px #007bff)";
            };
            playBtn.onmouseout = () => {
              playBtn.querySelector("img").style.filter = "";
            };

            // Nút pause
            const pauseBtn = document.createElement("button");
            pauseBtn.className = "play-btn-img";
            pauseBtn.title = "Tạm dừng";
            pauseBtn.style.background = "none";
            pauseBtn.style.border = "none";
            pauseBtn.style.outline = "none";
            pauseBtn.style.cursor = "pointer";
            pauseBtn.style.marginTop = "6px";
            pauseBtn.style.marginLeft = "8px";
            pauseBtn.style.display = "inline-flex";
            pauseBtn.style.alignItems = "center";
            pauseBtn.style.justifyContent = "center";
            pauseBtn.style.width = "32px";
            pauseBtn.style.height = "32px";
            pauseBtn.style.padding = "0";
            pauseBtn.innerHTML = `<img src='img/pause.svg' alt='Pause' style='width:28px;height:28px;transition:filter 0.2s;'>`;
            pauseBtn.onmouseover = () => {
              pauseBtn.querySelector("img").style.filter =
                "brightness(0.7) drop-shadow(0 0 4px #007bff)";
            };
            pauseBtn.onmouseout = () => {
              pauseBtn.querySelector("img").style.filter = "";
            };

            // Nút copy
            const copyBtn = document.createElement("button");
            copyBtn.className = "play-btn-img";
            copyBtn.title = "Sao chép nội dung";
            copyBtn.style.background = "none";
            copyBtn.style.border = "none";
            copyBtn.style.outline = "none";
            copyBtn.style.cursor = "pointer";
            copyBtn.style.marginTop = "6px";
            copyBtn.style.marginLeft = "8px";
            copyBtn.style.display = "inline-flex";
            copyBtn.style.alignItems = "center";
            copyBtn.style.justifyContent = "center";
            copyBtn.style.width = "32px";
            copyBtn.style.height = "32px";
            copyBtn.style.padding = "0";
            copyBtn.innerHTML = `<img src='img/copy.svg' alt='Copy' style='width:28px;height:28px;transition:filter 0.2s;'>`;
            copyBtn.onmouseover = () => {
              copyBtn.querySelector("img").style.filter =
                "brightness(0.7) drop-shadow(0 0 4px #007bff)";
            };
            copyBtn.onmouseout = () => {
              copyBtn.querySelector("img").style.filter = "";
            };
            copyBtn.onclick = () => {
              navigator.clipboard.writeText(message);
            };

            // Audio element (dùng chung cho play/pause)
            let audio = null;
            playBtn.onclick = () => {
              if (!audio) {
                audio = new Audio(audioUrl);
              }
              audio.play();
            };
            pauseBtn.onclick = () => {
              if (audio) {
                audio.pause();
              }
            };
            div.appendChild(document.createElement("br"));
            div.appendChild(playBtn);
            div.appendChild(pauseBtn);
            div.appendChild(copyBtn);
          }
        }
      };
      typeWriter();
    }
  }

  async function sendMessage() {
    const userText = input.value.trim();
    if (!userText) return;

    appendMessage("user", userText);
    input.value = "";

    // Xóa typing indicator cũ nếu có
    const oldTyping = document.getElementById("typing-indicator");
    if (oldTyping) oldTyping.remove();

    // Hiển thị hiệu ứng 3 dấu chấm tròn nhấp nháy
    const typingDiv = document.createElement("div");
    typingDiv.id = "typing-indicator";
    typingDiv.className = "typing-indicator";
    typingDiv.innerHTML = `
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    `;
    chatBox.appendChild(typingDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userText }),
      });
      const data = await res.json();
      typingDiv.remove();
      appendMessage("bot", data.answer.result, data.answer.audio_url);
    } catch (err) {
      typingDiv.remove();
      appendMessage("bot", "Đã xảy ra lỗi khi gửi câu trả lời.");
    }
  }

  sendBtn.addEventListener("click", sendMessage);

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});
