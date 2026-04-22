/**
 * Good Morning Murfreesboro — Contact form backend
 *
 * Receives form POSTs from goodmorningmurfreesboro.com, verifies the
 * Cloudflare Turnstile token, emails the submission to GMM, and optionally
 * logs it to a Google Sheet.
 *
 * Deploy:
 *   1. script.google.com -> New project -> paste this file
 *   2. Deploy -> New deployment -> Type: Web app
 *   3. Execute as: Me (your GMM Workspace account)
 *   4. Who has access: Anyone
 *   5. Copy the Web app URL -> paste into contact/index.html
 */

const CONFIG = {
  // Inbox that receives form submissions (GMM Workspace)
  TO_EMAIL: 'hello@goodmorningmurfreesboro.com',

  // From-name shown in the email header
  FROM_NAME: 'GMM Website',

  // Cloudflare Turnstile secret key (server-side verification)
  TURNSTILE_SECRET: '0x4AAAAAADBLWBJAkQ1DhOsK5JZ-MQ30O-k',

  // Optional: Sheet ID for logging (leave '' to skip). Get it from the
  // Sheet URL: docs.google.com/spreadsheets/d/<THIS_PART>/edit
  SHEET_ID: '',
};

function doPost(e) {
  try {
    const params = e.parameter || {};
    const formName = params['form-name'] || 'unknown';

    // Honeypot — silently accept so bots don't retry
    if (params['bot-field']) {
      return jsonResponse({ ok: true, note: 'bot-caught' });
    }

    // Turnstile verification
    const token = params['cf-turnstile-response'];
    if (!token || !verifyTurnstile(token)) {
      return jsonResponse({ ok: false, error: 'captcha-failed' });
    }

    // Email
    const { subject, body } = composeEmail(formName, params);
    MailApp.sendEmail({
      to: CONFIG.TO_EMAIL,
      subject: subject,
      body: body,
      replyTo: params.email || undefined,
      name: CONFIG.FROM_NAME,
    });

    // Optional logging
    if (CONFIG.SHEET_ID) logToSheet(formName, params);

    return jsonResponse({ ok: true });
  } catch (err) {
    console.error(err);
    return jsonResponse({ ok: false, error: String(err) });
  }
}

function doGet() {
  return jsonResponse({ ok: true, service: 'GMM contact backend' });
}

function verifyTurnstile(token) {
  const res = UrlFetchApp.fetch(
    'https://challenges.cloudflare.com/turnstile/v0/siteverify',
    {
      method: 'post',
      payload: { secret: CONFIG.TURNSTILE_SECRET, response: token },
      muteHttpExceptions: true,
    }
  );
  return JSON.parse(res.getContentText()).success === true;
}

function composeEmail(formName, params) {
  const titles = {
    'guest-spot': 'New Guest Spot Request',
    'nonprofit-request': 'New Non-Profit Feature Request',
    'general-contact': 'New Shoutout / General Message',
    'newsletter': 'New Newsletter Signup',
  };
  const subject = '[GMM Website] ' + (titles[formName] || 'Form: ' + formName);

  const skip = { 'cf-turnstile-response': 1, 'bot-field': 1, 'form-name': 1 };
  const when = new Date().toString();

  let body = 'Form: ' + formName + '\n';
  body += 'Submitted: ' + when + '\n';
  body += '----------------------------------------\n\n';

  Object.keys(params).forEach(function (key) {
    if (skip[key]) return;
    const label = key.replace(/_/g, ' ').replace(/\b\w/g, function (l) { return l.toUpperCase(); });
    body += label + ':\n' + params[key] + '\n\n';
  });

  return { subject: subject, body: body };
}

function logToSheet(formName, params) {
  const sheet = SpreadsheetApp.openById(CONFIG.SHEET_ID).getActiveSheet();
  sheet.appendRow([
    new Date(),
    formName,
    params.name || params.contact_person || '',
    params.email || '',
    params.phone || '',
    params.organization || params.business_name || '',
    params.message || params.mission || '',
    JSON.stringify(params),
  ]);
}

function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
