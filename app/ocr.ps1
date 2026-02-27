$imagePath = $args[0]
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Windows.Globalization
Add-Type -AssemblyName Windows.Graphics
Add-Type -AssemblyName Windows.Media

# Helper function to load Windows Runtime types
$ocr_class = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
$bitmap_class = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$file_class = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]

# Async await pattern in Powershell is tricky, using a simpler synchronous approach if possible or sync-over-async
# Loading image as software bitmap
$asTask = {
    param($path)
    $file = [Windows.Storage.StorageFile]::GetFileFromPathAsync($path).GetResults()
    $stream = $file.OpenAsync([Windows.Storage.FileAccessMode]::Read).GetResults()
    $decoder = [Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream).GetResults()
    $bitmap = $decoder.GetSoftwareBitmapAsync().GetResults()
    return $bitmap
}

# Create Engine
# 1. Prioritize Russian (ru) because it handles both Cyrillic and Latin well
try {
    $lang = [Windows.Globalization.Language]::new("ru")
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
    if ($null -ne $engine) {
        Write-Output "DEBUG: Forced 'ru' engine for better Cyrillic support."
    }
} catch {}

# 2. If 'ru' not found, try User Profile Languages
if ($null -eq $engine) {
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
}

# 3. If still null, try any available
if ($null -eq $engine) {
    Write-Output "DEBUG: UserProfileLanguages failed. Trying available languages..."
    
    $langs = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages
    foreach ($lang in $langs) {
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
        if ($null -ne $engine) {
            Write-Output "DEBUG: Created engine with language: $($lang.LanguageTag)"
            break
        }
    }
}

if ($null -eq $engine) {
    # Last ditch: Force en-US
    try {
        $lang = [Windows.Globalization.Language]::new("en-US")
        $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
    } catch {}
}

if ($null -eq $engine) {
    Write-Output "Error: OCR Engine totally failed to initialize."
    exit
}

try {
    # Get file (absolute path required)
    $fullPath = (Resolve-Path $imagePath).Path
    
    # Load Bitmap (Simplified for PS integration)
    # Note: Accessing WinRT async methods directly in PS 5.1 is hard.
    # We might need a slightly different approach or a compiled C# helper if this fails.
    # For now, let's try a proven PS snippet for OCR if available, 
    # OR fallback to the C# embedded in PS approach which is robust.
} catch {
    Write-Output "Error: $_"
}

# START C# EMBEDDED APPROACH (More Reliable)
$code = @"
using System;
using System.Threading.Tasks;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage;
using Windows.Storage.Streams;

public class OcrHelper {
    public static string ExtractText(string imagePath) {
        return Run(imagePath).GetAwaiter().GetResult();
    }

    private static async Task<string> Run(string imagePath) {
        try {
            StorageFile file = await StorageFile.GetFileFromPathAsync(imagePath);
            using (IRandomAccessStream stream = await file.OpenAsync(FileAccessMode.Read)) {
                BitmapDecoder decoder = await BitmapDecoder.CreateAsync(stream);
                SoftwareBitmap softwareBitmap = await decoder.GetSoftwareBitmapAsync();
                
                OcrEngine engine = OcrEngine.TryCreateFromUserProfileLanguages();
                if (engine == null) {
                     // Fallback to available languages
                    var languages = OcrEngine.AvailableRecognizerLanguages;
                    if (languages.Count > 0) {
                         engine = OcrEngine.TryCreateFromLanguage(languages[0]);
                    }
                }
                
                if (engine == null) return "Error: OCR Not Supported";

                var result = await engine.RecognizeAsync(softwareBitmap);
                return result.Text;
            }
        } catch (Exception ex) {
            return "Error: " + ex.Message;
        }
    }
}
"@

Add-Type -TypeDefinition $code -ReferencedAssemblies "System.Runtime.WindowsRuntime", "Windows.Foundation", "Windows.Globalization", "Windows.Graphics", "Windows.Media", "Windows.Storage"
[OcrHelper]::ExtractText($imagePath)
