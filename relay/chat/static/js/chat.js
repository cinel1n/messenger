    // Автоскролл к последнему сообщению при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        const messagesContainer = document.querySelector('.chat-mess');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    });

    base_url = `${window.location.hostname}:${window.location.port}`

    // Получаем UUID текущего чата
    const path_parts = window.location.pathname.split('/').filter(Boolean)
    const current_chat_uuid = path_parts.length >= 2 ? path_parts[1] : null

    // WebSocket для чата (только если есть открытый чат)
    let chatWebSocket = null

    if (current_chat_uuid) {
        chatWebSocket = new WebSocket(`ws://${base_url}/groups/${current_chat_uuid}/`)

        chatWebSocket.onopen = function (e) {
            console.log("Подключен к чату:", current_chat_uuid)
        }

        chatWebSocket.onmessage = function (e) {
            const data = JSON.parse(e.data)

            console.log("Получено сообщение:", data)

            if (data.type === "error") {
                showError(data.message)
                return
            }


            if (data.type === "chat_message" || data.type === "text_message") {
                // Добавляем сообщение в чат
                addMessageToChat(data.message, data.author)

                // Обновляем последнее сообщение в списке
                updateLastMessage(current_chat_uuid, data.message, data.author)
            }
        }

        chatWebSocket.onclose = function (e) {
            console.error('Chat socket closed')
            console.log("code:", e.code)
            console.log("reason:", e.reason)
            console.log("clean:", e.wasClean)
        }

        chatWebSocket.onerror = function(e) {
            console.error('WebSocket error:', e)
        }
    }

    function showError(message) {
        const errorDiv = document.querySelector('#ws-error')

        if (!errorDiv) return

        errorDiv.textContent = message
    }
    // Функция добавления сообщения в чат
    function addMessageToChat(content, sender) {
        const chatMessages = document.querySelector('.chat-mess')
        if (!chatMessages) return

        const isCurrentUser = sender === '{{ user.username }}'

        const messageDiv = document.createElement('div')
        messageDiv.className = isCurrentUser ? 'mes-1 mes-me' : 'mes-1'

        const avatar = document.createElement('img')
        avatar.className = 'avatar-user'
        avatar.src = "{% static 'image/Bez_foto_7.jpg' %}"

        const message = document.createElement('p')
        message.className = 'text-start text-break'
        message.textContent = content

        const time = document.createElement('span')
        time.textContent = new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        })

        messageDiv.appendChild(avatar)
        messageDiv.appendChild(message)
        messageDiv.appendChild(time)

        chatMessages.appendChild(messageDiv)
        chatMessages.scrollTop = chatMessages.scrollHeight
    }


    // Функция обновления последнего сообщения в списке
    function updateLastMessage(chat_uuid, message, sender) {
        const chatElement = document.getElementById(chat_uuid)
        if (!chatElement) return

        const lastMessageElem = chatElement.querySelector('.last-message')
        if (lastMessageElem) {
            const isCurrentUser = sender === '{{ user.username }}'
            const prefix = isCurrentUser ? "Вы: " : ""
            lastMessageElem.textContent = prefix + (message.length > 30 ?
                message.substring(0, 30) + '...' : message)
        }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        // Отправка сообщений (только если есть открытый чат)
        if (current_chat_uuid && chatWebSocket) {
            const messageInput = document.getElementById('message-input')
            const sendButton = document.getElementById('send-button')

            if (messageInput && sendButton) {
                // Автофокус
                messageInput.focus()

                // Отправка по кнопке
                sendButton.addEventListener('click', function(e) {
                    e.preventDefault()
                    sendMessage()
                })

                // Отправка по Enter
                messageInput.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault()
                        sendMessage()
                    }
                })

                function sendMessage() {
                    const content = messageInput.value.trim()
                    if (!content) {
                        alert('Введите сообщение!')
                        return
                    }

                    if (chatWebSocket.readyState === WebSocket.OPEN) {
                        console.log('Отправляю сообщение:', content)

                        chatWebSocket.send(JSON.stringify({
                            'type': "text_message",
                            'message': content
                        }))

                        // Очищаем поле
                        messageInput.value = ''
                        messageInput.focus()
                    } else {
                        console.error('WebSocket не подключен')
                        alert('Нет соединения с сервером!')
                    }
                }
            }
        }

        // Автоскролл к последним сообщениям
        const chatMessages = document.querySelector('.chat-mess')
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight
        }
    })

    document.addEventListener("DOMContentLoaded", function () {

    const button =
        document.getElementById("load-more-messages");

    const chatMessages =
        document.querySelector(".chat-mess");

    if (!button || !chatMessages) {
        return;
    }

    let nextCursor =
        chatMessages.dataset.nextCursor || null;

    let isLoading = false;


    button.addEventListener("click", async function () {

        if (isLoading || !nextCursor) {
            return;
        }

        isLoading = true;
        button.disabled = true;

        const oldScrollHeight =
            chatMessages.scrollHeight;

        const oldScrollTop =
            chatMessages.scrollTop;


        try {

            const url =
                "{% url 'chat-history' group.uuid %}" +
                "?before=" +
                encodeURIComponent(nextCursor);


            const response =
                await fetch(url);


            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }


            const data =
                await response.json();


            for (const item of data.messages) {

                const messageDiv =
                    document.createElement("div");

                messageDiv.className =
                    item.author === "{{ user.username }}"
                        ? "mes-1 mes-me"
                        : "mes-1";


                if (item.type === "message") {

                    const avatar =
                        document.createElement("img");

                    avatar.className =
                        "avatar-user";

                    avatar.src =
                        "{% static 'image/Bez_foto_7.jpg' %}";


                    const message =
                        document.createElement("p");

                    message.className =
                        "text-start text-break";

                    message.textContent =
                        item.content;


                    const time =
                        document.createElement("span");

                    time.textContent =
                        new Date(item.timestamp)
                            .toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit"
                            });


                    messageDiv.appendChild(avatar);
                    messageDiv.appendChild(message);
                    messageDiv.appendChild(time);

                }


                else if (item.type === "event") {

                    const message =
                        document.createElement("p");

                    message.className =
                        "text-start text-break";

                    message.textContent =
                        item.content;


                    const time =
                        document.createElement("span");

                    time.textContent =
                        new Date(item.timestamp)
                            .toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit"
                            });


                    messageDiv.appendChild(message);
                    messageDiv.appendChild(time);
                }


                chatMessages.prepend(messageDiv);
            }


            /*
             * Сохраняем положение пользователя
             * после добавления старых сообщений
             */
            const newScrollHeight =
                chatMessages.scrollHeight;

            chatMessages.scrollTop =
                oldScrollTop +
                (newScrollHeight - oldScrollHeight);


            /*
             * Получаем cursor для следующей загрузки
             */
            nextCursor =
                data.next_cursor || null;


            chatMessages.dataset.nextCursor =
                nextCursor || "";


            if (!nextCursor) {

                button.textContent =
                    "All messages have been loaded.";

                button.disabled = true;
            }


        } catch (error) {

            console.error(
                "error load messages:",
                error
            );

        } finally {

            isLoading = false;

            if (nextCursor) {
                button.disabled = false;
            }
        }
    });

});

