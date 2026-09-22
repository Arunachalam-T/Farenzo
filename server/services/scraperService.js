require('dotenv').config(); // Load the connection string from .env
const connectDB = require('../config/db'); // Load the database connection logic
const Fare = require('../models/Fare'); // Load the Fare schema we talked about!
const Route = require('../models/Route'); // Load the Route schema

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();

chromium.use(stealth);

async function runScraper() {
  console.log("🚀 Starting RedBus Scraper & MongoDB Saver...");
  
  // 1. Connect to MongoDB first!
  await connectDB();

  // 2. Ensure the Route exists in our Database
  // We check if "Chennai to Bangalore" exists. If not, we create it.
  // We need its unique ID (_id) because the Fare schema requires a routeId.
  let currentRoute = await Route.findOne({ fromCity: 'Chennai', toCity: 'Bangalore' });
  if (!currentRoute) {
    currentRoute = await Route.create({ fromCity: 'Chennai', toCity: 'Bangalore', distanceKm: 345 });
    console.log("✅ Created new Route in database.");
  }

  const targetDate = new Date();
  targetDate.setDate(targetDate.getDate() + 2);
  const dateOptions = { day: '2-digit', month: 'short', year: 'numeric' };
  const dateStr = targetDate.toLocaleDateString('en-GB', dateOptions).replace(/ /g, '-');
  
  const url = `https://www.redbus.in/bus-tickets/chennai-to-bangalore?fromCityName=Chennai&fromCityId=124&toCityName=Bangalore&toCityId=122&onward=${dateStr}`;
  
  const browser = await chromium.launch({ headless: 'new' });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
  });
  
  const page = await context.newPage();

  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(8000);
    await page.evaluate(() => window.scrollBy(0, 1500));
    await page.waitForTimeout(3000);

    const buses = await page.evaluate(() => {
      const results = [];
      const busItems = document.querySelectorAll('li[class*="tupleWrapper"]');
      
      busItems.forEach(item => {
        const ariaLabel = item.getAttribute('aria-label') || '';
        const regex = /^(.*?),\s*(.*?)\.\s*Departs\s*([\d:]+),\s*arrives\s*([\d:]+)\..*?Price\s*(\d+)\s*INR/i;
        const match = ariaLabel.match(regex);
        
        if (match) {
          results.push({
            operator: match[1].trim(),
            busType: match[2].trim(),
            departureTime: match[3].trim(),
            arrivalTime: match[4].trim(), // Extracted arrival time too!
            fare: parseInt(match[5]) || 0
          });
        }
      });
      return results;
    });

    if (buses.length > 0) {
      console.log(`🎉 Found ${buses.length} buses. Preparing to save to MongoDB...`);
      
      // 3. Format the data to match our Schema exactly
      const fareDocuments = buses.map(bus => ({
        routeId: currentRoute._id,          // Link to the Route
        fromCity: 'Chennai',
        toCity: 'Bangalore',
        operator: bus.operator,
        busType: bus.busType,
        departureTime: bus.departureTime,
        arrivalTime: bus.arrivalTime,
        fare: bus.fare,
        source: 'redbus',                   // Must be 'redbus' or 'abhibus' (per schema)
        journeyDate: targetDate,            // The actual travel date
        daysBeforeJourney: 2                // We scraped this 2 days in advance
      }));

      // 4. Check for duplicates before saving
      const existingCount = await Fare.countDocuments({
        fromCity: 'Chennai',
        toCity: 'Bangalore',
        journeyDate: { $gte: targetDate, $lt: new Date(targetDate.getTime() + 86400000) }
      });

      if (existingCount > 0) {
        console.log(`⚠️ Fares for this date already exist (${existingCount} records). Skipping insert to avoid duplicates.`);
      } else {
        await Fare.insertMany(fareDocuments);
        console.log(`✅ Successfully saved ${fareDocuments.length} fares to MongoDB!`);
      }
      
    } else {
      console.log("⚠️ No buses found.");
    }

  } catch (err) {
    console.error("❌ Error:", err.message);
  } finally {
    await browser.close();
    // 5. Always cleanly exit the database connection when done
    require('mongoose').connection.close(); 
  }
}

runScraper();
