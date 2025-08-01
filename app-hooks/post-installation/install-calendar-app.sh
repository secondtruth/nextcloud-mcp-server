#!/bin/bash

set -e  # Exit on any error

echo "Installing and configuring Calendar app..."

# Enable calendar app
php /var/www/html/occ app:enable calendar

# Wait for calendar app to be fully initialized
echo "Waiting for calendar app to initialize..."
sleep 10

# Ensure maintenance mode is off before calendar operations
php /var/www/html/occ maintenance:mode --off

# Create a default calendar for the admin user (may already exist, ignore errors)
echo "Creating default calendar..."
php /var/www/html/occ dav:create-calendar admin personal "Personal" "Default personal calendar" || true

# Sync DAV system to ensure proper initialization
echo "Syncing DAV system..."
php /var/www/html/occ dav:sync-system-addressbook

# Repair calendar app to ensure proper setup
echo "Repairing calendar app..."
php /var/www/html/occ maintenance:repair --include-expensive

# Final wait to ensure CalDAV service is fully ready
echo "Final CalDAV initialization wait..."
sleep 10

echo "Calendar app installation complete!"
