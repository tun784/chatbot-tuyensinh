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
      appendMessage("bot", data.answer.result);
      // if (data.answer && typeof data.answer === "string") {
      //   // Nếu data.answer là string (như trường hợp "Địa chỉ")
      //   appendMessage("bot", data.answer);
      // } else if (data.answer && data.answer.answer) {
      //   // Nếu data.answer là object chứa key 'answer'
      //   appendMessage("bot", data.answer.answer);
      // } else if (data.result) {
      //   // Nếu output của server là {'query': '...', 'result': '...'}
      //   appendMessage("bot", data.result);
      // } else {
      //   appendMessage(
      //     "bot",
      //     "Lỗi: Không nhận được câu trả lời đúng định dạng."
      //   );
      // }
    } catch (err) {
      appendMessage("bot", "Đã xảy ra lỗi khi gửi câu trả lời.");
    }
  }

  function appendMessage(sender, message) {
    const div = document.createElement("div");
    div.classList.add(sender === "user" ? "user-msg" : "bot-msg");

    const strong = document.createElement("strong");
    strong.textContent = sender === "user" ? "Bạn: " : "Chatbot: ";
    div.appendChild(strong);

    const span = document.createElement("span");
    div.appendChild(span);
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;

    if (sender === "user") {
      span.textContent = message;
    } else {
      let i = 0;
      const speed = 20; // Độ trễ giữa các ký tự (ms)
      const typeWriter = () => {
        if (i < message.length) {
          span.textContent += message.charAt(i);
          i++;
          chatBox.scrollTop = chatBox.scrollHeight;
          setTimeout(typeWriter, speed);
        }
      };
      typeWriter();
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
