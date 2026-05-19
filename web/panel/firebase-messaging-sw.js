importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-app-compat.js");
importScripts("https://www.gstatic.com/firebasejs/10.7.1/firebase-messaging-compat.js");

firebase.initializeApp({
  apiKey: "AIzaSyBOJzEPogIXtCagHesPIJrJsWrC2USSk0Y",
  authDomain: "citasflash-6e4ac.firebaseapp.com",
  projectId: "citasflash-6e4ac",
  messagingSenderId: "797428618621",
  appId: "1:797428618621:web:0b6deb831f220b76b72814"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(payload => {
  const {title, body} = payload.notification;
  self.registration.showNotification(title, {
    body,
    icon: "/panel/citasflash_icon_192.png"
  });
});
