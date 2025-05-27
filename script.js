document.addEventListener("DOMContentLoaded", function () {
  const input = document.getElementById("questionInput");
  const sendBtn = document.getElementById("sendButton");
  const chatBox = document.getElementById("chat-box");

  async function sendMessage() {
    const userText = input.value.trim();
    if (!userText) return;

    appendMessage("user", userText);
    input.value = "";

    try {
      const res = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: userText }),
      });

      const data = await res.json();
      appendMessage("bot", data.answer);
    } catch (err) {
      appendMessage("bot", "❌ Đã xảy ra lỗi khi gửi câu hỏi.");
    }
  }

  function appendMessage(sender, message) {
    const div = document.createElement("div");
    div.classList.add(sender === "user" ? "user-msg" : "bot-msg");
    div.innerHTML = `<strong>${
      sender === "user" ? "Bạn" : "Bot"
    }:</strong> ${message}`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  sendBtn.addEventListener("click", sendMessage);

  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});
