#include "ViewerPlayerController.h"
#include "Camera/CameraActor.h"
#include "Dom/JsonObject.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "InputKeyEventArgs.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "UnrealClient.h"

void AViewerPlayerController::SimulateKey(const FKey& Key, EInputEvent Event, float Amount)
{
    InputKey(FInputKeyEventArgs::CreateSimulated(Key, Event, Amount));
}

void AViewerPlayerController::FinishSmokeTest(bool bSuccess, const FString& Error)
{
    bSmokeTest = false;
    TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
    Report->SetStringField(TEXT("status"), bSuccess ? TEXT("success") : TEXT("failed"));
    Report->SetStringField(TEXT("error"), Error);
    Report->SetStringField(TEXT("map"), GetWorld()->GetMapName());
    Report->SetNumberField(TEXT("view_count"), Views.Num());
    Report->SetNumberField(TEXT("movement_cm"), SmokeDistance);
    Report->SetNumberField(TEXT("screen_percentage"), RenderPercentage);
    Report->SetBoolField(TEXT("preset_key_verified"), SmokeStage >= 3);
    Report->SetBoolField(TEXT("movement_key_verified"), SmokeStage >= 5);
    Report->SetBoolField(TEXT("look_axis_verified"), SmokeStage >= 6);
    Report->SetBoolField(TEXT("menu_key_verified"), SmokeStage >= 7);
    Report->SetStringField(TEXT("limitations"), TEXT("Fullscreen and mouse hit boxes require the windowed UI check."));
    if (GEngine && GEngine->GameViewport && GEngine->GameViewport->Viewport)
    {
        const FIntPoint Size = GEngine->GameViewport->Viewport->GetSizeXY();
        Report->SetNumberField(TEXT("width"), Size.X);
        Report->SetNumberField(TEXT("height"), Size.Y);
    }
    FString Json;
    TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
    FJsonSerializer::Serialize(Report, Writer);
    const bool bSaved = !SmokeDirectory.IsEmpty() &&
        FFileHelper::SaveStringToFile(Json, *(SmokeDirectory / TEXT("report.json")));
    if (!bSaved)
    {
        UE_LOG(LogPlatformViewer, Error, TEXT("Cannot write viewer smoke report."));
    }
    UE_LOG(LogPlatformViewer, Display, TEXT("VIEWER_SMOKE_%s %s"),
           bSuccess && bSaved ? TEXT("PASS") : TEXT("FAIL"), *Error);
    FPlatformMisc::RequestExitWithStatus(false, bSuccess && bSaved ? 0 : 1);
}

void AViewerPlayerController::TickSmokeTest(float DeltaSeconds)
{
    SmokeStageTime += DeltaSeconds;
    SmokeTotalTime += DeltaSeconds;
    if (SmokeTotalTime > 45.f)
    {
        FinishSmokeTest(false, TEXT("Viewer smoke test timed out."));
        return;
    }
    auto Advance = [this]() { ++SmokeStage; SmokeStageTime = 0.f; };
    switch (SmokeStage)
    {
    case 0:
        if (SmokeStageTime > 3.f)
        {
            if (!bReady || Views.Num() != 5 || !GetWorld()->GetMapName().Contains(TEXT("HiddenPlatform")))
            {
                FinishSmokeTest(false, TEXT("Wrong map or missing viewer presets."));
                return;
            }
            FScreenshotRequest::RequestScreenshot(SmokeDirectory / TEXT("01-main.png"), true, false);
            Advance();
        }
        break;
    case 1:
        if (IFileManager::Get().FileSize(*(SmokeDirectory / TEXT("01-main.png"))) > 1000)
        {
            SimulateKey(EKeys::Two, IE_Pressed, 1.f);
            Advance();
        }
        break;
    case 2:
        if (SmokeStageTime > .3f)
        {
            SimulateKey(EKeys::Two, IE_Released, 0.f);
            if (ActiveView != 1)
            {
                FinishSmokeTest(false, TEXT("Preset key did not reach Enhanced Input."));
                return;
            }
            FScreenshotRequest::RequestScreenshot(SmokeDirectory / TEXT("02-locomotive.png"), true, false);
            Advance();
        }
        break;
    case 3:
        if (IFileManager::Get().FileSize(*(SmokeDirectory / TEXT("02-locomotive.png"))) > 1000)
        {
            ToggleExplore();
            SmokeStartPosition = GetPawn()->GetActorLocation();
            SimulateKey(EKeys::W, IE_Pressed, 1.f);
            Advance();
        }
        break;
    case 4:
        if (SmokeStageTime > .6f)
        {
            SimulateKey(EKeys::W, IE_Released, 0.f);
            SmokeDistance = FVector::Distance(SmokeStartPosition, GetPawn()->GetActorLocation());
            if (SmokeDistance < 20.f || GetViewTarget() != GetPawn())
            {
                FinishSmokeTest(false, TEXT("Keyboard movement or exploration camera failed."));
                return;
            }
            SmokeStartRotation = GetControlRotation();
            SimulateKey(EKeys::MouseX, IE_Axis, 20.f);
            Advance();
        }
        break;
    case 5:
        if (SmokeStageTime > .2f)
        {
            if (FMath::Abs(FMath::FindDeltaAngleDegrees(SmokeStartRotation.Yaw, GetControlRotation().Yaw)) < .01f)
            {
                FinishSmokeTest(false, TEXT("Mouse look axis did not change camera rotation."));
                return;
            }
            SimulateKey(EKeys::Escape, IE_Pressed, 1.f);
            Advance();
        }
        break;
    case 6:
        if (SmokeStageTime > .2f)
        {
            SimulateKey(EKeys::Escape, IE_Released, 0.f);
            if (bExploring || !bShowMouseCursor)
            {
                FinishSmokeTest(false, TEXT("Menu key did not release the mouse."));
                return;
            }
            FScreenshotRequest::RequestScreenshot(SmokeDirectory / TEXT("03-explored.png"), true, false);
            Advance();
        }
        break;
    case 7:
        if (IFileManager::Get().FileSize(*(SmokeDirectory / TEXT("03-explored.png"))) > 1000)
        {
            FinishSmokeTest(true);
        }
        break;
    default:
        FinishSmokeTest(false, TEXT("Invalid smoke-test state."));
        break;
    }
}
