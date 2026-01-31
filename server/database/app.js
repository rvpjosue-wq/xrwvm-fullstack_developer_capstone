const express = require('express');
const mongoose = require('mongoose');
const fs = require('fs');
const cors = require('cors');

const app = express();
const port = 3030;

// Middleware
app.use(cors());
app.use(express.json()); // replaces express.raw + manual JSON.parse

// Load seed data
const reviews_data = JSON.parse(fs.readFileSync("reviews.json", "utf8"));
const dealerships_data = JSON.parse(fs.readFileSync("dealerships.json", "utf8"));

// MongoDB connection
mongoose.connect("mongodb://mongo_db:27017/", { dbName: "dealershipsDB" })
  .then(() => console.log("Connected to MongoDB"))
  .catch(err => console.error("MongoDB connection error:", err));

const Reviews = require('./review');
const Dealerships = require('./dealership');

// Seed database safely
async function seedDatabase() {
  try {
    await Reviews.deleteMany({});
    await Reviews.insertMany(reviews_data.reviews);

    await Dealerships.deleteMany({});
    await Dealerships.insertMany(dealerships_data.dealerships);

    console.log("Database seeded successfully");
  } catch (err) {
    console.error("Error seeding database:", err);
  }
}
seedDatabase();

// Home route
app.get('/', (req, res) => {
  res.send("Welcome to the Mongoose API");
});

// Fetch all reviews
app.get('/fetchReviews', async (req, res) => {
  try {
    const documents = await Reviews.find();
    res.json(documents);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching documents' });
  }
});

// Fetch reviews by dealer ID
app.get('/fetchReviews/dealer/:id', async (req, res) => {
  try {
    const documents = await Reviews.find({ dealership: req.params.id });
    res.json(documents);
  } catch (error) {
    res.status(500).json({ error: 'Error fetching documents' });
  }
});

// Fetch all dealerships
app.get('/fetchDealers', async (req, res) => {
  try {
    const dealers = await Dealerships.find();
    res.status(200).json(dealers);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch dealers" });
  }
});

// Fetch dealerships by state
app.get('/fetchDealers/:state', async (req, res) => {
    try {
        const documents = await Dealerships.find({state: req.params.state});
        res.json(documents);
      } catch (error) {
        res.status(500).json({ error: 'Error fetching documents' });
      }
    });


// Fetch a single dealer by ID
app.get('/fetchDealer/:id', async (req, res) => {
  const id = parseInt(req.params.id);

  try {
    const dealer = await Dealerships.findOne({ id });

    if (!dealer) {
      return res.status(404).json({ error: "Dealer not found" });
    }

    res.status(200).json(dealer);
  } catch (err) {
    res.status(500).json({ error: "Failed to fetch dealer by ID" });
  }
});

// Insert review
app.post('/insert_review', async (req, res) => {
  try {
    const data = req.body;

    const lastReview = await Reviews.findOne().sort({ id: -1 });
    const new_id = lastReview ? lastReview.id + 1 : 1;

    const review = new Reviews({
      id: new_id,
      name: data.name,
      dealership: data.dealership,
      review: data.review,
      purchase: data.purchase,
      purchase_date: data.purchase_date,
      car_make: data.car_make,
      car_model: data.car_model,
      car_year: data.car_year,
    });

    const savedReview = await review.save();
    res.json(savedReview);

  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error inserting review' });
  }
});

// Start server
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
