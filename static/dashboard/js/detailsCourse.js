 function previewFiles(input, previewContainerId) {
        const container = document.getElementById(previewContainerId);
        container.innerHTML = '';
        for (let i = 0; i < input.files.length; i++) {
          const fileDiv = document.createElement('div');
          fileDiv.textContent = input.files[i].name;
          container.appendChild(fileDiv);
        }
      }

function showNotification(message, type) {
  const notification = document.createElement('div')
  notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 1rem 1.5rem;
      border-radius: 12px;
      color: white;
      font-weight: 600;
      z-index: 1000;
      animation: slideIn 0.3s ease;
      box-shadow: 0 8px 25px rgba(0,0,0,0.15);
  `
  switch (type) {
    case 'success': notification.style.backgroundColor = 'var(--bs-green)'; break;
    case 'warning': notification.style.backgroundColor = 'var(--bs-pink)'; break;
    case 'info': notification.style.backgroundColor = 'var(--bs-cyan)'; break;
    default: notification.style.backgroundColor = '#333';
  }
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.style.animation = 'slideOut 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
}
function openModal(id) {
  document.getElementById(id).classList.remove('hidden');
}

function toggleResources(button) {
      const hiddenDiv = button.nextElementSibling;
      hiddenDiv.classList.toggle("hidden");
      button.textContent = hiddenDiv.classList.contains("hidden") ? "See more" : "See less";
}

function openResource(url, type) {
        if (type === "video") {
          window.open(url, "_blank");
        } else if (type === "pdf") {
          window.open(url, "_blank");
        } else if (type === "image") {
          const img = new Image();
          img.src = url;
          const w = window.open("");
          w.document.write(img.outerHTML);
        } else if (type === "audio") {
          const w = window.open("");
          w.document.write(`<audio controls autoplay src="${url}"></audio>`);
        } else {
          window.open(url, "_blank");
        }
}


// ✅ Ouvrir popup Add Lesson
document.querySelector('.add-lesson-btn').addEventListener('click', () => openModal('addLessonModal'));

// ✅ Ouvrir popup Add SubLesson
function openAddSubLessonModal(lessonId) {
  document.getElementById('subLessonLessonId').value = lessonId;
  openModal('addSubLessonModal');
}

// ✅ Gérer l’envoi du formulaire Add Lesson
document.getElementById('addLessonForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const res = await fetch("{% url 'add_lesson' %}", {
    method: 'POST',
    body: formData
  });
  if (res.ok) {
    alert('Lesson added successfully!');
    location.reload();
  } else {
    alert('Error adding lesson.');
  }
});

// ✅ Gérer l’envoi du formulaire Add SubLesson
document.getElementById('addSubLessonForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const res = await fetch("{% url 'add_sublesson' %}", {
    method: 'POST',
    body: formData
  });
  if (res.ok) {
    alert('Sublesson added successfully!');
    location.reload();
  } else {
    alert('Error adding sublesson.');
  }
});
function openUpdateLessonModal(id, title, description, resources) {
    document.getElementById('updateLessonId').value = id;
    document.getElementById('updateLessonTitle').value = title;
    document.getElementById('updateLessonDescription').value = description;

    let container = document.getElementById('updateLessonExistingResources');
    container.innerHTML = '';

    if (resources.length > 0) {
      resources.forEach(res => {
    container.innerHTML += `
        <div class="resource-item">
            <span>${res.title}</span>
            <button type="button" 
                    class="btn btn-edit" 
                    style="background-color: red; color: white;" 
                    onclick="removeResource(${res.id}, this)">
                Remove
            </button>
        </div>
    `;
});

    } else {
        container.innerHTML = '<p>No existing resources.</p>';
    }

    document.getElementById('updateLessonModal').classList.remove('hidden');
}

function removeResource(resourceId, button) {
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'delete_resources[]';
    input.value = resourceId;
    document.getElementById('updateLessonForm').appendChild(input);
    button.parentElement.remove();
}

function openUpdateSubLessonModal(id, title, content, resources, url) {
    document.getElementById('updateSubLessonId').value = id;
    document.getElementById('updateSubLessonTitle').value = title;
    document.getElementById('updateSubLessonContent').value = content;

    // Stocke l'URL sur le formulaire
    const form = document.getElementById('updateSubLessonForm');
    form.dataset.url = url;

    let container = document.getElementById('updateSubLessonExistingResources');
    container.innerHTML = '';

    if (resources && resources.length > 0) {
        resources.forEach(res => {
            container.innerHTML += `
                <div class="resource-item">
                    <span>${res.title}</span>
                    <button type="button" 
                            class="btn btn-edit" 
                            style="background-color: red; color: white;" 
                            onclick="removeSubResource(${res.id}, this)">
                        Remove
                    </button>
                </div>
            `;
        });
    } else {
        container.innerHTML = '<p>No existing resources.</p>';
    }

    document.getElementById('updateSubLessonModal').classList.remove('hidden');
}


function removeSubResource(resourceId, button) {
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'delete_resources[]';
    input.value = resourceId;
    document.getElementById('updateSubLessonForm').appendChild(input);
    button.parentElement.remove();
}



function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Helper to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
// Update Lesson
// Update Lesson
document.getElementById('updateLessonForm').addEventListener('submit', function(e){
    e.preventDefault();
    let formData = new FormData(this);

    // récupère l'URL depuis le bouton qui a ouvert le modal
    const url = document.querySelector('.btn-edit').dataset.url;

    fetch(url, {
        method: "POST",
        body: formData,
        headers: {'X-CSRFToken': formData.get('csrfmiddlewaretoken')}
    })
    .then(res => res.json())
    .then(data => {
        if(data.success){
            alert("Lesson updated successfully!");
            location.reload();
        } else {
            alert("Error updating lesson!");
        }
    });
});
document.getElementById('updateSubLessonForm').addEventListener('submit', function(e){
    e.preventDefault();
    let formData = new FormData(this);

    const url = this.dataset.url; // correctement défini maintenant

    fetch(url, {
        method: "POST",
        body: formData,
        headers: {'X-CSRFToken': formData.get('csrfmiddlewaretoken')}
    })
    .then(res => res.json())
    .then(data => {
        if(data.success){
            alert("SubLesson updated successfully!");
            location.reload();
        } else {
            alert("Error updating sublesson!");
        }
    });
});




function removeSubResource(resourceId, button) {
    let input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'delete_resources[]';
    input.value = resourceId;
    document.getElementById('updateSubLessonForm').appendChild(input);
    button.parentElement.remove();
}

// Delete confirmation
function confirmDeleteLesson(id) {
    if(confirm('Are you sure you want to delete this lesson?')) {
        fetch(`/teacherDash/lessons/${id}/delete/`, { method: 'POST', headers: {'X-CSRFToken': getCookie('csrftoken')} })
            .then(res => res.json())
            .then(data => { if(data.success) location.reload(); });
    }
}

function confirmDeleteSubLesson(id) {
    if(confirm('Are you sure you want to delete this sublesson?')) {
        fetch(`/teacherDash/sublessons/${id}/delete/`, { method: 'POST', headers: {'X-CSRFToken': getCookie('csrftoken')} })
            .then(res => res.json())
            .then(data => { if(data.success) location.reload(); });
    }
}

// Fonction pour récupérer le CSRFToken
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');





function openModal(id) {
    document.getElementById(id).classList.remove('hidden');
}
function closeModal(id) {
    document.getElementById(id).classList.add('hidden');
}