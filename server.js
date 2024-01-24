const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const path = require('path');
const session = require('express-session');
const crypto = require('crypto'); // Include the crypto module

const app = express();
const PORT = 3000;

// Function to generate a random string for the secret key
const generateRandomString = (length) => {
  return crypto.randomBytes(length).toString('hex');
};

const secretKey = generateRandomString(32); // Adjust the length as needed
console.log('Generated Secret Key:', secretKey);

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

app.use(session({
  secret: secretKey,
  resave: true,
  saveUninitialized: true
}));

mongoose.connect('mongodb://localhost:27017/Student_Details', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => console.log('MongoDB connected'))
.catch(err => console.error('MongoDB connection error:', err));

const UserSchema = new mongoose.Schema({
  first_name: String,
  last_name: String,
  email: String,
  password: String,
});

const User = mongoose.model('User', UserSchema);

app.use(express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public/register.html'));
});

app.post('/register', (req, res) => {
  const { first_name, last_name, email, password } = req.body;

  const newUser = new User({
    first_name,
    last_name,
    email,
    password,
  });

  newUser.save()
    .then(() => {
      res.redirect('/login.html');
    })
    .catch(err => res.status(500).send(`Error: ${err}`));
});

app.post('/login', (req, res) => {
  const { email, password } = req.body;

  User.findOne({ email })
    .then(user => {
      if (!user) {
        return res.status(404).send('User not found');
      }

      if (user.password !== password) {
        return res.status(401).send('Invalid password');
      }

      req.session.user = {
        email: user.email,
        first_name: user.first_name,
        last_name: user.last_name,
      };

      res.redirect('/student_dashboard.html');
    })
    .catch(err => res.status(500).send(`Error: ${err}`));
});

app.get('/dashboard', (req, res) => {
  const user = req.session.user;

  if (!user) {
    return res.status(401).send('Unauthorized');
  }

  res.sendFile(path.join(__dirname, 'student_dashboard.html'));
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
