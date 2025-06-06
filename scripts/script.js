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
            playBtn.innerHTML = `<img src='img/play.png' alt='Play' style='width:28px;height:28px;transition:filter 0.2s;'>`;
            playBtn.onmouseover = () => {
              playBtn.querySelector("img").style.filter =
                "brightness(0.7) drop-shadow(0 0 4px #007bff)";
            };
            playBtn.onmouseout = () => {
              playBtn.querySelector("img").style.filter = "";
            };
            playBtn.onclick = () => {
              const audio = new Audio(audioUrl);
              audio.play();
            };
            div.appendChild(document.createElement("br"));
            div.appendChild(playBtn);
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
      const res = await fetch("/chat", {
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
