#include "ViewerHUD.h"
#include "ViewerPlayerController.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"

void AViewerHUD::DrawHUD()
{
    Super::DrawHUD();
    AViewerPlayerController* Viewer = Cast<AViewerPlayerController>(PlayerOwner);
    if (!Canvas || !Viewer)
    {
        return;
    }
    const float Scale = FMath::Clamp(Canvas->ClipX / 1536.f, .65f, 1.5f);
    const float Margin = 24.f * Scale;
    if (!Viewer->GetViewerError().IsEmpty())
    {
        DrawRect(FLinearColor(.08f, .01f, .01f, .95f), Margin, Margin, 850.f * Scale, 100.f * Scale);
        DrawText(Viewer->GetViewerError(), FLinearColor::White, Margin + 16 * Scale, Margin + 16 * Scale,
                 GEngine->GetMediumFont(), Scale);
        return;
    }
    if (!Viewer->AreControlsVisible())
    {
        return;
    }
    const float Width = FMath::Min(950.f * Scale, Canvas->ClipX - 2 * Margin);
    const float Height = 154.f * Scale;
    const float Y = Canvas->ClipY - Height - Margin;
    DrawRect(FLinearColor(.012f, .017f, .018f, .88f), Margin, Y, Width, Height);
    DrawRect(FLinearColor(.56f, .32f, .11f, 1.f), Margin, Y, 3.f * Scale, Height);
    const float X = Margin + 18.f * Scale;
    DrawText(TEXT("PLATFORM NINE"), FLinearColor(.90f, .73f, .47f), X, Y + 10 * Scale,
             GEngine->GetLargeFont(), .9f * Scale);
    DrawText(TEXT("Original Unreal environment study  |  Work in progress"), FLinearColor(.72f, .75f, .75f),
             X, Y + 41 * Scale, GEngine->GetSmallFont(), Scale);
    const FString Status = FString::Printf(TEXT("%s  |  1-5 preset views  |  H hide controls  |  F11 fullscreen"),
                                           *Viewer->GetViewLabel());
    DrawText(Status, FLinearColor::White, X, Y + 62 * Scale, GEngine->GetSmallFont(), Scale);
    if (Viewer->IsExploring())
    {
        DrawText(TEXT("WASD + mouse to explore   Q/E or Ctrl/Space vertical   Shift faster   Esc menu"),
                 FLinearColor(.80f, .83f, .83f), X, Y + 96 * Scale, GEngine->GetSmallFont(), Scale);
    }
    else
    {
        const TArray<FName> Names = {TEXT("Explore"), TEXT("Next"), TEXT("Fullscreen"), TEXT("Quit")};
        const TArray<FString> Labels = {TEXT("Explore  [Tab]"), TEXT("Next view"), TEXT("Fullscreen"), TEXT("Quit")};
        for (int32 Index = 0; Index < Names.Num(); ++Index)
        {
            const float ButtonX = X + Index * 166.f * Scale;
            const float ButtonY = Y + 101.f * Scale;
            DrawRect(FLinearColor(.12f, .15f, .15f, 1.f), ButtonX, ButtonY, 150.f * Scale, 34.f * Scale);
            DrawText(Labels[Index], FLinearColor::White, ButtonX + 10 * Scale, ButtonY + 7 * Scale,
                     GEngine->GetSmallFont(), Scale);
            AddHitBox(FVector2D(ButtonX, ButtonY), FVector2D(150.f * Scale, 34.f * Scale), Names[Index], true);
        }
    }
}

void AViewerHUD::NotifyHitBoxClick(FName BoxName)
{
    Super::NotifyHitBoxClick(BoxName);
    if (AViewerPlayerController* Viewer = Cast<AViewerPlayerController>(PlayerOwner))
    {
        if (BoxName == TEXT("Explore")) { Viewer->ToggleExplore(); }
        else if (BoxName == TEXT("Next")) { Viewer->NextView(); }
        else if (BoxName == TEXT("Fullscreen")) { Viewer->ToggleFullscreen(); }
        else if (BoxName == TEXT("Quit")) { Viewer->QuitViewer(); }
    }
}
