FROM nginx:alpine
WORKDIR /usr/share/nginx/html
COPY index.html style.css app.js ./
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
