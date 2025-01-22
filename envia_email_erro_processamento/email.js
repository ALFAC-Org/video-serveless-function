
const nodemailer = require('nodemailer');

const enviaEmail = async (email, videoName) => {
    // Criar o transporter
    let transporter = nodemailer.createTransport({
        host: 'smtp.gmail.com',
        port: 465,
        secure: true,
        auth: {
            user: process.env.ALFAC_ORG_EMAIL,
            pass: process.env.ALFAC_ORG_EMAIL_PASSWORD
        }
    });
    console.log('Transporter criado');
    
    // Definir as opções do email
    let mailOptions = {
        from: process.env.ALFAC_ORG_EMAIL,
        to: email,
        subject: 'noreply: Erro no processamento do vídeo',
        text: `Você está recebendo essa mensagem porque houve um erro no processamento do seu vídeo - ${videoName}. Verifique a plataforma e tente novamente.`
    };
    console.log('MailOptions criado');


    // Enviar o email
    try {
        let info = await transporter.sendMail(mailOptions);
        console.log('Email enviado: ' + info.response);
    } catch (error) {
        console.log(error);
    }
}


exports.enviaEmail = enviaEmail;