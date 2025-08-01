const express = require('express');
const router = express.Router();
const db = require('../database/connection');

// Initialize database connection
db.connect().catch(console.error);

// GET /api/stats - Get overall statistics
router.get('/', async (req, res) => {
  try {
    // Get overall file statistics
    const fileStatsQuery = `
      SELECT 
        COUNT(*) as total_files,
        SUM(CASE WHEN mime_type LIKE 'image%' THEN 1 ELSE 0 END) as total_images,
        SUM(CASE WHEN mime_type LIKE 'video%' THEN 1 ELSE 0 END) as total_videos,
        SUM(CASE WHEN mime_type LIKE 'image%' AND processing_status = 'completed' THEN 1 ELSE 0 END) as images_completed,
        SUM(CASE WHEN mime_type LIKE 'image%' AND processing_status = 'pending' THEN 1 ELSE 0 END) as images_pending,
        SUM(CASE WHEN mime_type LIKE 'image%' AND processing_status = 'failed' THEN 1 ELSE 0 END) as images_failed,
        SUM(CASE WHEN mime_type LIKE 'image%' AND processing_status = 'in_progress' THEN 1 ELSE 0 END) as images_in_progress
      FROM files
    `;

    const fileStats = await db.get(fileStatsQuery);

    // Get quality distribution
    const qualityDistQuery = `
      SELECT 
        visual_quality,
        COUNT(*) as count
      FROM metadata
      WHERE visual_quality IS NOT NULL
      GROUP BY visual_quality
      ORDER BY visual_quality
    `;

    const qualityDistribution = await db.query(qualityDistQuery);

    // Get social media score distribution
    const socialDistQuery = `
      SELECT 
        social_media_score,
        COUNT(*) as count
      FROM metadata
      WHERE social_media_score IS NOT NULL
      GROUP BY social_media_score
      ORDER BY social_media_score
    `;

    const socialDistribution = await db.query(socialDistQuery);

    // Get marketing score distribution
    const marketingDistQuery = `
      SELECT 
        marketing_score,
        COUNT(*) as count
      FROM metadata
      WHERE marketing_score IS NOT NULL
      GROUP BY marketing_score
      ORDER BY marketing_score
    `;

    const marketingDistribution = await db.query(marketingDistQuery);

    // Get activity tag counts
    const tagCountsQuery = `
      SELECT 
        tag_name,
        COUNT(DISTINCT file_id) as count
      FROM activity_tags
      GROUP BY tag_name
      ORDER BY count DESC
    `;

    const tagCounts = await db.query(tagCountsQuery);

    // Get season distribution
    const seasonDistQuery = `
      SELECT 
        season,
        COUNT(*) as count
      FROM metadata
      WHERE season IS NOT NULL AND season != 'unclear'
      GROUP BY season
      ORDER BY 
        CASE season
          WHEN 'spring' THEN 1
          WHEN 'summer' THEN 2
          WHEN 'fall' THEN 3
          WHEN 'winter' THEN 4
        END
    `;

    const seasonDistribution = await db.query(seasonDistQuery);

    // Get people statistics
    const peopleStatsQuery = `
      SELECT 
        SUM(CASE WHEN has_people = 1 THEN 1 ELSE 0 END) as with_people,
        SUM(CASE WHEN has_people = 0 THEN 1 ELSE 0 END) as without_people,
        people_count,
        COUNT(*) as count
      FROM metadata
      WHERE people_count IS NOT NULL
      GROUP BY people_count
      ORDER BY 
        CASE people_count
          WHEN 'none' THEN 0
          WHEN '1-2' THEN 1
          WHEN '3-5' THEN 2
          WHEN '6-10' THEN 3
          WHEN '10+' THEN 4
        END
    `;

    const peopleStats = await db.query(peopleStatsQuery);

    // Get recent processing activity
    const recentActivityQuery = `
      SELECT 
        DATE(processed_at) as date,
        COUNT(*) as processed_count
      FROM files
      WHERE processed_at IS NOT NULL
      AND DATE(processed_at) >= DATE('now', '-30 days')
      GROUP BY DATE(processed_at)
      ORDER BY date DESC
    `;

    const recentActivity = await db.query(recentActivityQuery);

    // Calculate processing rate
    const processingRateQuery = `
      SELECT 
        COUNT(*) as last_24h_processed
      FROM files
      WHERE processed_at >= datetime('now', '-24 hours')
      AND processing_status = 'completed'
    `;

    const processingRate = await db.get(processingRateQuery);

    res.json({
      fileStats,
      qualityDistribution,
      socialDistribution,
      marketingDistribution,
      tagCounts,
      seasonDistribution,
      peopleStats,
      recentActivity,
      processingRate: processingRate.last_24h_processed || 0,
      lastUpdated: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/stats/summary - Get quick summary stats
router.get('/summary', async (req, res) => {
  try {
    const summaryQuery = `
      SELECT 
        (SELECT COUNT(*) FROM files WHERE mime_type LIKE 'image%') as total_images,
        (SELECT COUNT(*) FROM files WHERE mime_type LIKE 'image%' AND processing_status = 'completed') as processed_images,
        (SELECT COUNT(*) FROM files WHERE mime_type LIKE 'image%' AND processing_status = 'pending') as pending_images,
        (SELECT AVG(visual_quality) FROM metadata WHERE visual_quality IS NOT NULL) as avg_quality,
        (SELECT AVG(social_media_score) FROM metadata WHERE social_media_score IS NOT NULL) as avg_social_score,
        (SELECT AVG(marketing_score) FROM metadata WHERE marketing_score IS NOT NULL) as avg_marketing_score,
        (SELECT COUNT(DISTINCT tag_name) FROM activity_tags) as unique_tags_used,
        (SELECT COUNT(*) FROM metadata WHERE has_people = 1) as images_with_people
    `;

    const summary = await db.get(summaryQuery);

    // Calculate completion percentage
    const completionPercentage = summary.total_images > 0 
      ? Math.round((summary.processed_images / summary.total_images) * 100)
      : 0;

    res.json({
      ...summary,
      avg_quality: summary.avg_quality ? parseFloat(summary.avg_quality.toFixed(2)) : 0,
      avg_social_score: summary.avg_social_score ? parseFloat(summary.avg_social_score.toFixed(2)) : 0,
      avg_marketing_score: summary.avg_marketing_score ? parseFloat(summary.avg_marketing_score.toFixed(2)) : 0,
      completion_percentage: completionPercentage
    });

  } catch (error) {
    console.error('Error fetching summary stats:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;