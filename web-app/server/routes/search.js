const express = require('express');
const router = express.Router();
const db = require('../database/connection');

// Initialize database connection
db.connect().catch(console.error);

// POST /api/search - Advanced search with filters
router.post('/', async (req, res) => {
  try {
    const {
      query = '',
      visualQuality = [1, 5],
      hasPeople,
      peopleCount = [],
      isIndoor,
      activityTags = [],
      season = [],
      timeOfDay = [],
      socialMediaScore = [1, 5],
      marketingScore = [1, 5],
      minWidth,
      maxWidth,
      minHeight,
      maxHeight,
      aspectRatio = 'any',
      page = 1,
      limit = 20,
      sort = 'created_date',
      order = 'DESC'
    } = req.body;

    const offset = (parseInt(page) - 1) * parseInt(limit);

    // Build the main query
    let searchQuery = `
      SELECT 
        f.id,
        f.filename,
        f.file_path,
        f.file_size,
        f.width,
        f.height,
        f.mime_type,
        f.created_date,
        f.modified_date,
        f.thumbnail_path,
        f.drive_file_id,
        f.processing_status,
        f.processed_at,
        m.primary_subject,
        m.visual_quality,
        m.has_people,
        m.people_count,
        m.is_indoor,
        m.social_media_score,
        m.social_media_reason,
        m.marketing_score,
        m.marketing_use,
        m.season,
        m.time_of_day,
        m.mood_energy,
        m.color_palette,
        m.notes,
        m.extracted_at
      FROM files f
      LEFT JOIN metadata m ON f.id = m.file_id
      WHERE f.mime_type LIKE 'image%' 
      AND f.processing_status = 'completed'
    `;

    const params = [];

    // Text search
    if (query.trim()) {
      searchQuery += ` AND (
        m.primary_subject LIKE ? OR 
        f.filename LIKE ? OR 
        m.notes LIKE ? OR
        m.marketing_use LIKE ? OR
        m.social_media_reason LIKE ?
      )`;
      const searchTerm = `%${query.trim()}%`;
      params.push(searchTerm, searchTerm, searchTerm, searchTerm, searchTerm);
    }

    // Visual quality range
    if (visualQuality && visualQuality.length === 2) {
      searchQuery += ` AND m.visual_quality BETWEEN ? AND ?`;
      params.push(visualQuality[0], visualQuality[1]);
    }

    // People filters
    if (hasPeople !== undefined) {
      searchQuery += ` AND m.has_people = ?`;
      params.push(hasPeople);
    }

    if (peopleCount && peopleCount.length > 0) {
      const placeholders = peopleCount.map(() => '?').join(',');
      searchQuery += ` AND m.people_count IN (${placeholders})`;
      params.push(...peopleCount);
    }

    // Indoor/outdoor filter
    if (isIndoor !== undefined) {
      searchQuery += ` AND m.is_indoor = ?`;
      params.push(isIndoor);
    }

    // Season filter
    if (season && season.length > 0) {
      const placeholders = season.map(() => '?').join(',');
      searchQuery += ` AND m.season IN (${placeholders})`;
      params.push(...season);
    }

    // Time of day filter
    if (timeOfDay && timeOfDay.length > 0) {
      const placeholders = timeOfDay.map(() => '?').join(',');
      searchQuery += ` AND m.time_of_day IN (${placeholders})`;
      params.push(...timeOfDay);
    }

    // Social media score range
    if (socialMediaScore && socialMediaScore.length === 2) {
      searchQuery += ` AND m.social_media_score BETWEEN ? AND ?`;
      params.push(socialMediaScore[0], socialMediaScore[1]);
    }

    // Marketing score range
    if (marketingScore && marketingScore.length === 2) {
      searchQuery += ` AND m.marketing_score BETWEEN ? AND ?`;
      params.push(marketingScore[0], marketingScore[1]);
    }

    // Dimension filters
    if (minWidth !== undefined && minWidth !== null) {
      searchQuery += ` AND f.width >= ?`;
      params.push(minWidth);
    }

    if (maxWidth !== undefined && maxWidth !== null) {
      searchQuery += ` AND f.width <= ?`;
      params.push(maxWidth);
    }

    if (minHeight !== undefined && minHeight !== null) {
      searchQuery += ` AND f.height >= ?`;
      params.push(minHeight);
    }

    if (maxHeight !== undefined && maxHeight !== null) {
      searchQuery += ` AND f.height <= ?`;
      params.push(maxHeight);
    }

    // Aspect ratio filter
    if (aspectRatio && aspectRatio !== 'any') {
      if (aspectRatio === 'landscape') {
        searchQuery += ` AND f.width > f.height`;
      } else if (aspectRatio === 'portrait') {
        searchQuery += ` AND f.height > f.width`;
      } else if (aspectRatio === 'square') {
        searchQuery += ` AND abs(f.width - f.height) < (CASE WHEN f.width > f.height THEN f.width ELSE f.height END) * 0.1`;
      }
    }

    // Activity tags filter
    if (activityTags && activityTags.length > 0) {
      const placeholders = activityTags.map(() => '?').join(',');
      searchQuery += ` AND f.id IN (
        SELECT DISTINCT file_id 
        FROM activity_tags 
        WHERE tag_name IN (${placeholders})
      )`;
      params.push(...activityTags);
    }

    // Add sorting
    const validSortColumns = ['created_date', 'filename', 'visual_quality', 'social_media_score', 'marketing_score'];
    const validOrders = ['ASC', 'DESC'];
    
    if (validSortColumns.includes(sort) && validOrders.includes(order.toUpperCase())) {
      const sortColumn = sort === 'created_date' ? 'f.created_date' : 
                        sort === 'filename' ? 'f.filename' :
                        `m.${sort}`;
      searchQuery += ` ORDER BY ${sortColumn} ${order.toUpperCase()}`;
    }

    // Add pagination
    searchQuery += ` LIMIT ? OFFSET ?`;
    params.push(parseInt(limit), offset);

    const images = await db.query(searchQuery, params);

    // Get activity tags for each image
    const imageIds = images.map(img => img.id);
    let allActivityTags = [];
    
    if (imageIds.length > 0) {
      const placeholders = imageIds.map(() => '?').join(',');
      const tagsQuery = `
        SELECT file_id, tag_name 
        FROM activity_tags 
        WHERE file_id IN (${placeholders})
      `;
      allActivityTags = await db.query(tagsQuery, imageIds);
    }

    // Group tags by file_id
    const tagsByFileId = allActivityTags.reduce((acc, tag) => {
      if (!acc[tag.file_id]) acc[tag.file_id] = [];
      acc[tag.file_id].push(tag.tag_name);
      return acc;
    }, {});

    // Add activity tags to images and generate URLs
    const imagesWithTags = images.map(image => ({
      ...image,
      activity_tags: tagsByFileId[image.id] || [],
      drive_view_url: `https://drive.google.com/file/d/${image.drive_file_id}/view`,
      drive_download_url: `https://drive.google.com/uc?id=${image.drive_file_id}`
    }));

    // Get total count for pagination (run same query without LIMIT/OFFSET)
    let countQuery = searchQuery.replace(/SELECT.*?FROM/s, 'SELECT COUNT(DISTINCT f.id) as total FROM');
    countQuery = countQuery.replace(/ORDER BY.*$/s, '');
    countQuery = countQuery.replace(/LIMIT.*$/s, '');
    
    const countParams = params.slice(0, -2); // Remove LIMIT and OFFSET params
    const totalResult = await db.get(countQuery, countParams);
    const total = totalResult.total;

    res.json({
      images: imagesWithTags,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / parseInt(limit))
      },
      filters: {
        query,
        visualQuality,
        hasPeople,
        peopleCount,
        isIndoor,
        activityTags,
        season,
        timeOfDay,
        socialMediaScore,
        marketingScore,
        minWidth,
        maxWidth,
        minHeight,
        maxHeight,
        aspectRatio
      }
    });

  } catch (error) {
    console.error('Error in search:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// GET /api/search/suggestions - Get search suggestions based on existing data
router.get('/suggestions', async (req, res) => {
  try {
    const { q } = req.query;
    
    if (!q || q.length < 2) {
      return res.json({ suggestions: [] });
    }

    const searchTerm = `%${q}%`;
    
    // Get suggestions from primary_subject, filename, and notes
    const query = `
      SELECT DISTINCT
        CASE 
          WHEN primary_subject LIKE ? THEN primary_subject
          WHEN filename LIKE ? THEN filename
          WHEN notes LIKE ? THEN notes
        END as suggestion
      FROM files f
      LEFT JOIN metadata m ON f.id = m.file_id
      WHERE (primary_subject LIKE ? OR filename LIKE ? OR notes LIKE ?)
      AND f.processing_status = 'completed'
      AND suggestion IS NOT NULL
      ORDER BY suggestion
      LIMIT 10
    `;

    const suggestions = await db.query(query, [
      searchTerm, searchTerm, searchTerm,
      searchTerm, searchTerm, searchTerm
    ]);

    res.json({
      suggestions: suggestions.map(row => row.suggestion)
    });

  } catch (error) {
    console.error('Error getting suggestions:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;