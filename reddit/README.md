# Reddit Ingestion Service

This service fetches finance-related posts and comments from Reddit subreddits and saves them as JSONL files.

## Configuration

Edit the `.conf` file to specify which subreddits to monitor:

```bash
SUBREDDITS=investing+stocks+StockMarket+EuropeFIRE+PersonalFinanceEurope
```

## Environment Variables

Make sure you have the following environment variables in your root `.env` file:

```bash
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_user_agent
```

## Running with Docker

### Build and run:
```bash
docker-compose up --build
```

### Run in background:
```bash
docker-compose up -d --build
```

### View logs:
```bash
docker-compose logs -f
```

## Output

The service will create JSONL files in the `output/` directory with Reddit posts and their top comments.

## Customization

You can customize the script behavior by modifying the command in `docker-compose.yml`:

```yaml
command: ["python", "reddit_ingestion.py", "--limit", "100", "--time", "day"]
```

Available parameters:
- `--subs`: Subreddits to search (default from .conf file)
- `--q`: Search query (default: finance-related terms)
- `--time`: Time filter (hour, day, week, month, year, all)
- `--limit`: Number of posts to fetch
- `--out`: Output file path
- `--top_n`: Number of top comments per post
- `--max_depth`: Comment reply depth
- `--max_replies`: Maximum replies per comment level
