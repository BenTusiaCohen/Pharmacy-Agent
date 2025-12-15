const chatEl = document.getElementById("chat");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");

let messages = []; // Stateless: stored only in the browser

function addMessage(role, content) {
  const wrap = document.createElement("div");
  wrap.className = "msg";

  const roleEl = document.createElement("div");
  roleEl.className = "role";
  roleEl.textContent = role;

  const contentEl = document.createElement("div");
  contentEl.className = role === "assistant" ? "assistant" : "";
  contentEl.textContent = content;

  wrap.appendChild(roleEl);
  wrap.appendChild(contentEl);
  chatEl.appendChild(wrap);
  chatEl.scrollTop = chatEl.scrollHeight;

  return contentEl;
}

async function send() {
  const userText = inputEl.value.trim();
  if (!userText) return;
  inputEl.value = "";

  messages.push({ role: "user", content: userText });
  addMessage("user", userText);

  const assistantContentEl = addMessage("assistant", "");

  const res = await fetch("/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages })
  });

  const reader = res.body.getReader();
  const decoder = new TextDecoder();

  let assistantText = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    assistantText += chunk;
    assistantContentEl.textContent = assistantText;
    chatEl.scrollTop = chatEl.scrollHeight;
  }

  messages.push({ role: "assistant", content: assistantText });
}

sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});
