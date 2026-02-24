# Deployment Guide: Vercel & Neon PostgreSQL

This guide explains how to deploy the MTB School & College Management System to Vercel and connect it to a Neon serverless PostgreSQL database.

## Step 1: Set up Neon PostgreSQL
1. Go to [Neon.tech](https://neon.tech/) and create a free account.
2. Create a new project (e.g., "mtb-school-db").
3. Once the database is created, you will see a **Connection String** (Database URL) that looks like:
   `postgresql://username:password@ep-lucky-breeze-123456.us-east-2.aws.neon.tech/neondb?sslmode=require`
4. Copy this Connection String. You will need it in Step 2.

## Step 2: Push Your Code to GitHub
We have already initialized your Git repository and committed all the files locally.
If we used the GitHub CLI automatically, your repository should be up on your GitHub account.

If it failed to push automatically, you can push it manually via Terminal:
```bash
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/mtb-school.git
git push -u origin main
```

## Step 3: Deploy to Vercel
1. Go to [Vercel.com](https://vercel.com/) and sign in with your GitHub account.
2. Click **Add New** -> **Project**.
3. Import your `mtb-school` repository from GitHub.
4. In the **Configure Project** section:
   - **Framework Preset**: leave as "Other" (Vercel will detect the `vercel.json` file we created).
   - Expand the **Environment Variables** section. Add the following variables:
     - `FLASK_ENV` = `production`
     - `SECRET_KEY` = `your-super-secret-key-12345` (Make up a secure string here)
     - `DATABASE_URL` = Paste your Neon connection string from Step 1 here. **Replace `postgres://` or `postgresql://` with `postgresql://`**.
5. Click **Deploy**. Vercel will build your application and assign you a live URL.

## Step 4: Seed the Database on Vercel (Optional)
Since it's a completely new Neon database, you'll want to initialize the tables. Because Vercel functions are stateless and we can't easily run CLI commands over SSH, the easiest way to initialize the Neon DB is to run the initialization locally *against* the remote Neon database just once:

1. On your local machine, open your `.env` file.
2. Change the `DATABASE_URL` locally to match your Neon Connection String.
3. Open your terminal in the project folder and run:
   ```bash
   flask seed-db
   ```
4. This will create all the required PostgreSQL tables inside Neon and insert the demo admin accounts.
5. (Don't forget to change your local `.env` `DATABASE_URL` back to SQLite if you want to continue testing locally).

## Step 5: Important Notes on Vercel Serverless
- **File Uploads**: Vercel Serverless Functions have an ephemeral (temporary) filesystem. Uploading files (like student photos) or generating physical PDF files directly to `/static/uploads` won't persist across requests. You may need to eventually modify the system to use AWS S3, Cloudinary, or Supabase Storage for persistent file uploads if this goes to high-scale production.
- **Face Recognition**: The `face_recognition` Python library requires C++ compilation (dlib, cmake) which exceeds the standard 250MB size limit of free Vercel functions. Vercel is great for Flask, but heavy AI models might require hosting the API on Render or Railway if you face build-size limits. If you face a deployment size error on Vercel, consider deploying on **Render.com** instead, which supports Docker and heavy dependencies seamlessly!
