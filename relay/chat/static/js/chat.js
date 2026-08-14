
    base_url = `${window.location.hostname}:${window.location.port}`
    
    const currentUser = "{{ user.username|escapejs }}";
    console.log('Текущий пользователь:', currentUser);
    
    const path_parts = window.location.pathname.split('/').filter(Boolean)
    const current_chat_uuid = path_parts.length >= 2 ? path_parts[1] : null
    
    let chatWebSocket = null
    
    if (current_chat_uuid) {
        chatWebSocket = new WebSocket(`ws://${base_url}/groups/${current_chat_uuid}/`)
        
        chatWebSocket.onopen = function (e) {
            console.log("Подключен к чату:", current_chat_uuid)
        }
        
        chatWebSocket.onmessage = function (e) {
            const data = JSON.parse(e.data)
            console.log("Получено сообщение:", data)
            
            if (data.type === "text_message" || data.type === "chat_message") {
                addMessageToChat(data.message, data.author)
                updateLastMessage(current_chat_uuid, data.message, data.author)
            }
        }

        chatWebSocket.onclose = function (e) {
            console.error('Chat socket closed')
        }
    }

    // Функция добавления сообщения в чат
    function addMessageToChat(content, sender) {
        const chatMessages = document.querySelector('.chat-mess')
        if (!chatMessages) return

        const isCurrentUser = sender === currentUser  // ✅ Используем переменную

        const messageDiv = document.createElement('div')
        messageDiv.className = isCurrentUser ? 'mes-1 mes-me' : 'mes-1'

        const time = new Date().toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        })

        messageDiv.innerHTML = `
            <img class="avatar-user" src="{% static 'image/Bez_foto_7.jpg' %}">
            <p class="text-start text-break">${content}</p>
            <span>${time}</span>
        `

        chatMessages.appendChild(messageDiv)
        chatMessages.scrollTop = chatMessages.scrollHeight
    }

    // Функция обновления последнего сообщения в списке
    function updateLastMessage(chat_uuid, message, sender) {
        const chatElement = document.getElementById(chat_uuid)
        if (!chatElement) return

        const lastMessageElem = chatElement.querySelector('.last-message')
        if (lastMessageElem) {
            const isCurrentUser = sender === currentUser  // ✅ Используем переменную
            const prefix = isCurrentUser ? "Вы: " : ""
            lastMessageElem.textContent = prefix + (message.length > 30 ?
                message.substring(0, 30) + '...' : message)

            chatElement.style.backgroundColor = '#e8f5e8'
            setTimeout(() => {
                chatElement.style.backgroundColor = ''
            }, 3000)
        }
    }

    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        if (current_chat_uuid && chatWebSocket) {
            const messageInput = document.getElementById('message-input')
            const sendButton = document.getElementById('send-button')
            
            if (messageInput && sendButton) {
                messageInput.focus()
                
                sendButton.addEventListener('click', function(e) {
                    e.preventDefault()
                    sendMessage()
                })
                
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
                        console.log('Отправляю сообщение от:', currentUser)
                        
                        // ✅ ПРАВИЛЬНО: используем переменную currentUser
                        chatWebSocket.send(JSON.stringify({
                            'type': "text_message",
                            'author': currentUser,
                            'message': content
                        }))
                        
                        messageInput.value = ''
                        messageInput.focus()
                    } else {
                        console.error('WebSocket не подключен')
                    }
                }
            }
        }
        
        // Автоскролл
        const chatMessages = document.querySelector('.chat-mess')
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight
        }
    })
