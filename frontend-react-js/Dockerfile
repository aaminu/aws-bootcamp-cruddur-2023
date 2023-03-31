ARG image_name

FROM ${image_name}

ENV PORT=3000

COPY . /frontend-react-js
WORKDIR /frontend-react-js
RUN npm install
    
EXPOSE ${PORT}
CMD ["npm", "start"]