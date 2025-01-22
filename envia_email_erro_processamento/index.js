
const { enviaEmail } = require("./email.js")

const handler = async (event) => {
    // Acessando os atributos da mensagem SNS
    const email = event.Records[0].Sns.MessageAttributes.email.Value;
    const videoName = event.Records[0].Sns.MessageAttributes.video_name.Value;

    await enviaEmail(email, videoName);
};

exports.handler = handler