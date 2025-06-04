document.addEventListener("DOMContentLoaded", function () {
    const questionInput = document.getElementById("questionInput");
    const sendButton = document.getElementById("sendButton");
    const chatBox = document.getElementById("chat-box");
    const typingIndicator = document.getElementById("typing-indicator");

    // Hàm gửi tin nhắn
    async function sendMessage() {
      const userText = questionInput.value.trim();
      if (!userText) return; // Không gửi nếu input trống

      appendMessage("user", userText);
      questionInput.value = ""; // Xóa input sau khi gửi
      questionInput.focus(); // Focus lại vào input
      typingIndicator.style.display = "block"; // Hiển thị "Bot đang soạn tin..."
      chatBox.scrollTop = chatBox.scrollHeight; // Cuộn xuống cuối

      try {
        const response = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: userText }),
        });

        typingIndicator.style.display = "none"; // Ẩn "Bot đang soạn tin..."

        if (!response.ok) {
          // Xử lý lỗi HTTP (ví dụ: 500 Internal Server Error)
          const errorData = await response.json().catch(() => null); // Cố gắng parse lỗi JSON
          const errorMessage =
            errorData && errorData.error
              ? errorData.error
              : `Lỗi máy chủ: ${response.status}. Vui lòng thử lại sau.`;
          appendMessage("bot", errorMessage, true); // true để đánh dấu là tin nhắn lỗi
          console.error("Server error:", response.status, errorData);
          return;
        }

        const data = await response.json();

        if (data.error) {
          // Xử lý lỗi logic từ server (ví dụ: "Câu hỏi không được để trống")
          appendMessage("bot", data.error, true);
          console.error("Application error:", data.error);
        } else if (data.answer && data.answer.result) {
          // Hiển thị câu trả lời từ bot với hiệu ứng typing
          appendMessage("bot", data.answer.result);
        } else if (data.answer && typeof data.answer === "string") {
          // Fallback nếu answer là string trực tiếp (ít khả năng xảy ra với cấu trúc hiện tại)
          appendMessage("bot", data.answer);
        } else {
          appendMessage(
            "bot",
            "Xin lỗi, tôi không thể xử lý câu trả lời lúc này. Phản hồi không đúng định dạng.",
            true
          );
          console.error("Unexpected response format:", data);
        }
      } catch (err) {
        typingIndicator.style.display = "none"; // Ẩn "Bot đang soạn tin..."
        appendMessage(
          "bot",
          "Đã xảy ra lỗi kết nối hoặc xử lý. Vui lòng thử lại sau.",
          true
        );
        console.error("Fetch error:", err);
      }
    }

    // Hàm thêm tin nhắn vào chat box
    function appendMessage(sender, message, isError = false) {
      const messageDiv = document.createElement("div");
      messageDiv.classList.add(sender === "user" ? "user-msg" : "bot-msg");
      if (isError && sender === "bot") {
        messageDiv.classList.add("error-msg"); // Thêm class cho tin nhắn lỗi của bot
      }

      const messageSpan = document.createElement("span");
      messageDiv.appendChild(messageSpan);
      chatBox.appendChild(messageDiv);

      // Hiệu ứng typing cho tin nhắn của bot (không phải lỗi)
      if (sender === "bot" && !isError) {
        let i = 0;
        const speed = 10; // Tốc độ typing (ms mỗi ký tự)
        function typeWriter() {
          if (i < message.length) {
            messageSpan.textContent += message.charAt(i);
            i++;
            chatBox.scrollTop = chatBox.scrollHeight; // Luôn cuộn xuống khi thêm ký tự
            setTimeout(typeWriter, speed);
          }
        }
        typeWriter();
      } else {
        messageSpan.textContent = message; // Hiển thị ngay cho user hoặc lỗi của bot
      }
      chatBox.scrollTop = chatBox.scrollHeight; // Cuộn xuống cuối cùng
    }

    // Gửi tin nhắn khi nhấn nút "Gửi"
    sendButton.addEventListener("click", sendMessage);

    // Gửi tin nhắn khi nhấn Enter trong input (trừ Shift + Enter)
    questionInput.addEventListener("keydown", function (event) {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault(); // Ngăn hành vi mặc định của Enter (xuống dòng trong textarea)
        sendMessage();
      }
    });

    // Focus vào input khi trang được tải
    questionInput.focus();
  }
);
