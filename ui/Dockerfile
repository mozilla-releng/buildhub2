# Note! If you make changes it in this file, to rebuild it use:
#   docker-compose build ui
#

FROM node:10.16.0-slim@sha256:3af9a90272f938005513b14872b573265568f446a89523b5f5d30ca60dc8e29c as ui

ADD ui/package.json /package.json
ADD ui/yarn.lock /yarn.lock
RUN yarn

ENV NODE_PATH=/node_modules
ENV PATH=$PATH:/node_modules/.bin

WORKDIR /app
ADD ui /app

EXPOSE 3000
EXPOSE 35729

ENTRYPOINT ["/bin/bash", "/app/run.sh"]
CMD ["start"]
