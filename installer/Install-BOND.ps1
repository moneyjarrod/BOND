# BOND v2.0.0 Installer -- Custom WPF Wizard
# Compile with: ps2exe -inputFile Install-BOND.ps1 -outputFile BOND_Setup.exe -noConsole -title "BOND Setup" -version "2.0.0"
# Source: C:\Projects\BOND_parallel

param(
    [string]$SourceRoot = "C:\Projects\BOND_parallel"
)

Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName System.Windows.Forms

# ── XAML UI ───────────────────────────────────────────────────

[xml]$xaml = @'
<Window
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    Title="BOND Setup"
    Width="640" Height="480"
    WindowStartupLocation="CenterScreen"
    ResizeMode="NoResize"
    Background="#1a1a2e">

    <Window.Resources>
        <Style TargetType="TextBlock">
            <Setter Property="Foreground" Value="#e0e0e0"/>
            <Setter Property="FontFamily" Value="Segoe UI"/>
        </Style>
        <Style TargetType="Button" x:Key="NavBtn">
            <Setter Property="Background" Value="#16213e"/>
            <Setter Property="Foreground" Value="#e0e0e0"/>
            <Setter Property="BorderBrush" Value="#0f3460"/>
            <Setter Property="Padding" Value="20,8"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="Cursor" Value="Hand"/>
            <Setter Property="Template">
                <Setter.Value>
                    <ControlTemplate TargetType="Button">
                        <Border Background="{TemplateBinding Background}"
                                BorderBrush="{TemplateBinding BorderBrush}"
                                BorderThickness="1" CornerRadius="4"
                                Padding="{TemplateBinding Padding}">
                            <ContentPresenter HorizontalAlignment="Center" VerticalAlignment="Center"/>
                        </Border>
                        <ControlTemplate.Triggers>
                            <Trigger Property="IsMouseOver" Value="True">
                                <Setter Property="Background" Value="#0f3460"/>
                            </Trigger>
                            <Trigger Property="IsEnabled" Value="False">
                                <Setter Property="Opacity" Value="0.4"/>
                            </Trigger>
                        </ControlTemplate.Triggers>
                    </ControlTemplate>
                </Setter.Value>
            </Setter>
        </Style>
        <Style TargetType="Button" x:Key="AccentBtn" BasedOn="{StaticResource NavBtn}">
            <Setter Property="Background" Value="#e94560"/>
            <Setter Property="BorderBrush" Value="#e94560"/>
            <Setter Property="FontWeight" Value="SemiBold"/>
            <Style.Triggers>
                <Trigger Property="IsMouseOver" Value="True">
                    <Setter Property="Background" Value="#c73e54"/>
                </Trigger>
            </Style.Triggers>
        </Style>
        <Style TargetType="CheckBox">
            <Setter Property="Foreground" Value="#e0e0e0"/>
            <Setter Property="FontSize" Value="13"/>
            <Setter Property="Margin" Value="0,4"/>
        </Style>
    </Window.Resources>

    <Grid>
        <Grid.RowDefinitions>
            <RowDefinition Height="60"/>
            <RowDefinition Height="*"/>
            <RowDefinition Height="50"/>
        </Grid.RowDefinitions>

        <!-- Header -->
        <Border Grid.Row="0" Background="#16213e" BorderBrush="#0f3460" BorderThickness="0,0,0,1">
            <StackPanel Orientation="Horizontal" VerticalAlignment="Center" Margin="20,0">
                <TextBlock Text="BOND" FontSize="22" FontWeight="Bold" Foreground="#e94560"/>
                <TextBlock Text=" v2.0.0 Setup" FontSize="22" Foreground="#e0e0e0"/>
            </StackPanel>
        </Border>

        <!-- Pages -->
        <Grid Grid.Row="1" Margin="30,20">

            <!-- Page 0: Welcome -->
            <StackPanel x:Name="PageWelcome" Visibility="Visible">
                <TextBlock Text="Your AI forgets you every conversation." FontSize="18" FontWeight="SemiBold" Margin="0,10,0,15"/>
                <TextBlock TextWrapping="Wrap" FontSize="13" LineHeight="22" Margin="0,0,0,15">
                    BOND fixes that. It gives Claude persistent memory, structured projects,
                    and a protocol where you both agree before anything changes.
                </TextBlock>
                <TextBlock TextWrapping="Wrap" FontSize="13" LineHeight="22" Margin="0,0,0,15">
                    This wizard will set up your workspace -- the daemon that tracks state,
                    the entity system that organizes your work, and the connection to Claude.
                </TextBlock>
                <TextBlock TextWrapping="Wrap" FontSize="13" LineHeight="22" Foreground="#999">
                    No admin rights required. Your data stays on your machine.
                </TextBlock>
            </StackPanel>

            <!-- Page 1: Prerequisites -->
            <StackPanel x:Name="PagePrereqs" Visibility="Collapsed">
                <TextBlock Text="Checking your system" FontSize="18" FontWeight="SemiBold" Margin="0,10,0,15"/>
                <StackPanel x:Name="PrereqList" Margin="0,5">
                    <StackPanel Orientation="Horizontal" Margin="0,6">
                        <TextBlock x:Name="PythonStatus" Text="[?]" FontSize="14" Width="30" FontFamily="Consolas"/>
                        <TextBlock Text="Python 3.8+" FontSize="13" VerticalAlignment="Center"/>
                        <TextBlock x:Name="PythonVersion" FontSize="12" Foreground="#888" Margin="10,0" VerticalAlignment="Center"/>
                    </StackPanel>
                    <StackPanel Orientation="Horizontal" Margin="0,6">
                        <TextBlock x:Name="NodeStatus" Text="[?]" FontSize="14" Width="30" FontFamily="Consolas"/>
                        <TextBlock Text="Node.js 18+ (for panel)" FontSize="13" VerticalAlignment="Center"/>
                        <TextBlock x:Name="NodeVersion" FontSize="12" Foreground="#888" Margin="10,0" VerticalAlignment="Center"/>
                    </StackPanel>
                </StackPanel>
                <TextBlock x:Name="PrereqMessage" TextWrapping="Wrap" FontSize="12" Foreground="#e94560" Margin="0,15,0,0"/>
            </StackPanel>

            <!-- Page 2: Directory -->
            <StackPanel x:Name="PageDirectory" Visibility="Collapsed">
                <TextBlock Text="Where should BOND live?" FontSize="18" FontWeight="SemiBold" Margin="0,10,0,15"/>
                <TextBlock TextWrapping="Wrap" FontSize="13" Margin="0,0,0,15">
                    Choose a folder for your BOND installation. This is where your entities,
                    doctrine, and session data will be stored.
                </TextBlock>
                <Grid Margin="0,5">
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>
                    <TextBox x:Name="InstallPath" Grid.Column="0"
                             Background="#0a0a1a" Foreground="#e0e0e0" BorderBrush="#0f3460"
                             FontSize="13" Padding="8,6" VerticalContentAlignment="Center"/>
                    <Button x:Name="BrowseBtn" Grid.Column="1" Content="Browse..."
                            Style="{StaticResource NavBtn}" Margin="8,0,0,0"/>
                </Grid>
                <TextBlock x:Name="PathWarning" TextWrapping="Wrap" FontSize="12" Foreground="#e94560" Margin="0,10,0,0"/>
            </StackPanel>

            <!-- Page 3: Components -->
            <StackPanel x:Name="PageComponents" Visibility="Collapsed">
                <TextBlock Text="What to install" FontSize="18" FontWeight="SemiBold" Margin="0,10,0,15"/>
                <CheckBox x:Name="ChkCore" Content="BOND Core (daemon, doctrine, SKILL, QAIS, ISS)" IsChecked="True" IsEnabled="False"/>
                <TextBlock Text="    Required. The engine that makes everything work." FontSize="11" Foreground="#888" Margin="0,0,0,8"/>
                <CheckBox x:Name="ChkPanel" Content="Control Panel (React dashboard)" IsChecked="True"/>
                <TextBlock Text="    Visual dashboard for managing entities and sessions. Requires Node.js." FontSize="11" Foreground="#888" Margin="0,0,0,8"/>
                <CheckBox x:Name="ChkBridge" Content="AHK Clipboard Bridge + Counter" IsChecked="True"/>
                <TextBlock Text="    Clipboard integration and session counter display." FontSize="11" Foreground="#888" Margin="0,0,0,8"/>
            </StackPanel>

            <!-- Page 4: Transfer -->
            <StackPanel x:Name="PageTransfer" Visibility="Collapsed">
                <TextBlock Text="Transfer existing data?" FontSize="18" FontWeight="SemiBold" Margin="0,10,0,15"/>
                <TextBlock x:Name="V1PathText" TextWrapping="Wrap" FontSize="13" Margin="0,0,0,8"/>
                <TextBlock TextWrapping="Wrap" FontSize="13" LineHeight="22" Margin="0,0,0,10">
                    If you have an existing BOND installation, your personal data
                    (entities, perspectives, handoffs, session history) can be transferred.
                    A full backup is created first. The original is never modified.
                </TextBlock>
                <CheckBox x:Name="ChkTransfer" Content="Transfer data from an existing installation" IsChecked="False"/>
                <Grid Margin="20,8,0,0">
                    <Grid.ColumnDefinitions>
                        <ColumnDefinition Width="*"/>
                        <ColumnDefinition Width="Auto"/>
                    </Grid.ColumnDefinitions>
                    <TextBox x:Name="V1BrowsePath" Grid.Column="0"
                             Background="#0a0a1a" Foreground="#e0e0e0" BorderBrush="#0f3460"
                             FontSize="12" Padding="8,6" VerticalContentAlignment="Center"
                             IsEnabled="False"/>
                    <Button x:Name="V1BrowseBtn" Grid.Column="1" Content="Browse..."
                            Style="{StaticResource NavBtn}" Margin="8,0,0,0" IsEnabled="False"/>
                </Grid>
                <TextBlock TextWrapping="Wrap" FontSize="11" Foreground="#888" Margin="20,8,0,0">
                    Point to the folder containing your existing BOND (should have doctrine/ and SKILL.md).
                    Link arrays will be emptied during transfer (v2 architecture).
                </TextBlock>
                <TextBlock TextWrapping="Wrap" FontSize="11" Foreground="#999" Margin="20,4,0,0">
                    Skip this if this is your first time using BOND.
                </TextBlock>
            </StackPanel>

            <!-- Page 5: Installing -->
            <StackPanel x:Name="PageInstalling" Visibility="Collapsed">
                <TextBlock Text="Setting up your workspace" FontSize="18" FontWeight="SemiBold" Margin="0,10,0,15"/>
                <TextBlock x:Name="InstallStatus" Text="Preparing..." FontSize="13" Margin="0,0,0,10"/>
                <ProgressBar x:Name="InstallProgress" Height="8" Minimum="0" Maximum="100"
                             Background="#0a0a1a" Foreground="#e94560" BorderBrush="#0f3460"/>
                <TextBlock x:Name="InstallDetail" TextWrapping="Wrap" FontSize="11" Foreground="#888" Margin="0,10,0,0"/>
            </StackPanel>

            <!-- Page 6: Done -->
            <StackPanel x:Name="PageDone" Visibility="Collapsed">
                <TextBlock Text="You're all set." FontSize="18" FontWeight="SemiBold" Margin="0,10,0,15"/>
                <TextBlock TextWrapping="Wrap" FontSize="13" LineHeight="22" Margin="0,0,0,10">
                    BOND is installed and ready. Here's what to do next:
                </TextBlock>
                <TextBlock FontSize="13" LineHeight="24" Margin="10,0,0,10" TextWrapping="Wrap">
                    1. Add the MCP config to your Claude settings
                    2. Copy SKILL.md into your Claude Project system prompt
                    3. Start the daemon
                    4. Type {Sync} in Claude
                </TextBlock>
                <TextBlock x:Name="McpSnippetPath" TextWrapping="Wrap" FontSize="11" Foreground="#888" Margin="0,10,0,0"/>
                <TextBlock x:Name="TransferReportPath" TextWrapping="Wrap" FontSize="11" Foreground="#888" Margin="0,4,0,0"/>
            </StackPanel>
        </Grid>

        <!-- Navigation -->
        <Border Grid.Row="2" Background="#16213e" BorderBrush="#0f3460" BorderThickness="0,1,0,0">
            <Grid Margin="20,0">
                <Button x:Name="BtnBack" Content="Back" Style="{StaticResource NavBtn}" HorizontalAlignment="Left" VerticalAlignment="Center"/>
                <Button x:Name="BtnNext" Content="Next" Style="{StaticResource AccentBtn}" HorizontalAlignment="Right" VerticalAlignment="Center"/>
            </Grid>
        </Border>
    </Grid>
</Window>
'@

# ── WINDOW SETUP ──────────────────────────────────────────────

$reader = New-Object System.Xml.XmlNodeReader $xaml
$window = [Windows.Markup.XamlReader]::Load($reader)

# Get all named elements
$PageWelcome = $window.FindName("PageWelcome")
$PagePrereqs = $window.FindName("PagePrereqs")
$PageDirectory = $window.FindName("PageDirectory")
$PageComponents = $window.FindName("PageComponents")
$PageTransfer = $window.FindName("PageTransfer")
$PageInstalling = $window.FindName("PageInstalling")
$PageDone = $window.FindName("PageDone")

$PythonStatus = $window.FindName("PythonStatus")
$PythonVersion = $window.FindName("PythonVersion")
$NodeStatus = $window.FindName("NodeStatus")
$NodeVersion = $window.FindName("NodeVersion")
$PrereqMessage = $window.FindName("PrereqMessage")

$InstallPath = $window.FindName("InstallPath")
$BrowseBtn = $window.FindName("BrowseBtn")
$PathWarning = $window.FindName("PathWarning")

$ChkCore = $window.FindName("ChkCore")
$ChkPanel = $window.FindName("ChkPanel")
$ChkBridge = $window.FindName("ChkBridge")

$V1PathText = $window.FindName("V1PathText")
$ChkTransfer = $window.FindName("ChkTransfer")
$V1BrowsePath = $window.FindName("V1BrowsePath")
$V1BrowseBtn = $window.FindName("V1BrowseBtn")

$InstallStatus = $window.FindName("InstallStatus")
$InstallProgress = $window.FindName("InstallProgress")
$InstallDetail = $window.FindName("InstallDetail")

$McpSnippetPath = $window.FindName("McpSnippetPath")
$TransferReportPath = $window.FindName("TransferReportPath")

$BtnBack = $window.FindName("BtnBack")
$BtnNext = $window.FindName("BtnNext")

# ── STATE ─────────────────────────────────────────────────────

$script:CurrentPage = 0
$script:V1Path = ""
$script:V1Detected = $false
$script:PythonOK = $false
$script:TotalPages = 6 # 0-6, but 4 (transfer) is conditional

$InstallPath.Text = "C:\BOND"

$Pages = @($PageWelcome, $PagePrereqs, $PageDirectory, $PageComponents, $PageTransfer, $PageInstalling, $PageDone)

# ── HELPER FUNCTIONS ──────────────────────────────────────────

function Show-Page($index) {
    for ($i = 0; $i -lt $Pages.Count; $i++) {
        if ($i -eq $index) { $Pages[$i].Visibility = "Visible" }
        else { $Pages[$i].Visibility = "Collapsed" }
    }
    $script:CurrentPage = $index

    # Nav button state
    switch ($index) {
        0 { $BtnBack.Visibility = "Hidden"; $BtnNext.Content = "Get Started" }
        1 { $BtnBack.Visibility = "Visible"; $BtnNext.Content = "Next"; $BtnNext.IsEnabled = $script:PythonOK }
        2 { $BtnBack.Visibility = "Visible"; $BtnNext.Content = "Next" }
        3 { $BtnBack.Visibility = "Visible"; $BtnNext.Content = "Install" }
        4 { $BtnBack.Visibility = "Visible"; $BtnNext.Content = "Install" }
        5 { $BtnBack.Visibility = "Hidden"; $BtnNext.Visibility = "Hidden" }
        6 { $BtnBack.Visibility = "Hidden"; $BtnNext.Content = "Close"; $BtnNext.Visibility = "Visible" }
    }
}

function Check-Prerequisites {
    # Python
    try {
        $pyOut = & python --version 2>&1
        $pyVer = "$pyOut".Trim()
        $PythonStatus.Text = "[OK]"
        $PythonStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
        $PythonVersion.Text = $pyVer
        $script:PythonOK = $true
    } catch {
        $PythonStatus.Text = "[X]"
        $PythonStatus.Foreground = [System.Windows.Media.Brushes]::Red
        $PythonVersion.Text = "Not found"
        $PrereqMessage.Text = "Python 3.8+ is required. Install from https://python.org (check 'Add to PATH')."
        $script:PythonOK = $false
    }

    # Node
    try {
        $nodeOut = & node --version 2>&1
        $nodeVer = "$nodeOut".Trim()
        $NodeStatus.Text = "[OK]"
        $NodeStatus.Foreground = [System.Windows.Media.Brushes]::LimeGreen
        $NodeVersion.Text = $nodeVer
    } catch {
        $NodeStatus.Text = "[--]"
        $NodeStatus.Foreground = [System.Windows.Media.Brushes]::Yellow
        $NodeVersion.Text = "Not found (panel will be skipped)"
    }

    $BtnNext.IsEnabled = $script:PythonOK
}

function Detect-V1 {
    $testPaths = @("C:\BOND", "$env:USERPROFILE\Desktop\BOND", "$env:USERPROFILE\Documents\BOND")
    foreach ($tp in $testPaths) {
        if ((Test-Path (Join-Path $tp "doctrine")) -and (Test-Path (Join-Path $tp "SKILL.md")) -and -not (Test-Path (Join-Path $tp "transition\REPLACED.md"))) {
            $script:V1Path = $tp
            $script:V1Detected = $true
            return
        }
    }
    $script:V1Detected = $false
}

function Update-Status($status, $detail, $pct) {
    $InstallStatus.Text = $status
    $InstallDetail.Text = $detail
    $InstallProgress.Value = $pct
    $window.Dispatcher.Invoke([Action]{}, [System.Windows.Threading.DispatcherPriority]::Background)
}

function Install-Skeleton {
    $dest = $InstallPath.Text

    Update-Status "Creating directories..." "" 5

    # Create directory structure
    $dirs = @("doctrine", "doctrine\BOND_MASTER", "doctrine\PROJECT_MASTER", "templates", "templates\classes", "templates\entities", "search_daemon", "QAIS", "ISS", "state", "data", "data\perspectives", "handoffs", "installer", "transition", "docs", "platforms", "platforms\claude-code")
    if ($ChkPanel.IsChecked) { $dirs += @("panel") }
    if ($ChkBridge.IsChecked) { $dirs += @("bridge") }

    foreach ($d in $dirs) {
        $p = Join-Path $dest $d
        if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
    }

    Update-Status "Copying core files..." "" 15

    # Root files
    $rootFiles = @("SKILL.md", "GETTING_STARTED.md", "CHANGELOG.md", "start_bond.bat", "stop_bond.bat", "start_daemon.bat", "start_daemon.sh", "stop_daemon.bat", "warm_restore.py", "install_bond.bat")
    foreach ($f in $rootFiles) {
        $src = Join-Path $SourceRoot $f
        if (Test-Path $src) { Copy-Item $src (Join-Path $dest $f) -Force }
    }

    Update-Status "Copying daemon..." "" 25
    Copy-Item (Join-Path $SourceRoot "search_daemon\*") (Join-Path $dest "search_daemon") -Recurse -Force

    Update-Status "Copying QAIS server..." "" 35
    Copy-Item (Join-Path $SourceRoot "QAIS\*") (Join-Path $dest "QAIS") -Recurse -Force

    Update-Status "Copying ISS server..." "" 40
    Copy-Item (Join-Path $SourceRoot "ISS\*") (Join-Path $dest "ISS") -Recurse -Force

    Update-Status "Copying doctrine..." "" 50
    Copy-Item (Join-Path $SourceRoot "doctrine\BOND_MASTER\*") (Join-Path $dest "doctrine\BOND_MASTER") -Recurse -Force
    Copy-Item (Join-Path $SourceRoot "doctrine\PROJECT_MASTER\*") (Join-Path $dest "doctrine\PROJECT_MASTER") -Recurse -Force

    Update-Status "Copying templates..." "" 55
    Copy-Item (Join-Path $SourceRoot "templates\*") (Join-Path $dest "templates") -Recurse -Force

    # State defaults
    $cfgPath = Join-Path $dest "state\config.json"
    if (-not (Test-Path $cfgPath)) {
        '{"save_confirmation": true, "platform": "windows"}' | Set-Content $cfgPath -Encoding ASCII
    }
    $aePath = Join-Path $dest "state\active_entity.json"
    '{"entity": null, "path": null}' | Set-Content $aePath -Encoding ASCII

    # Data files
    Update-Status "Copying data files..." "" 60
    $dataFiles = @("iss_projections.npz", "iss_projections_st.npz", "limbic_genome.json", "limbic_genome_10d.json", "qais_field.npz")
    foreach ($f in $dataFiles) {
        $src = Join-Path $SourceRoot "data\$f"
        if (Test-Path $src) { Copy-Item $src (Join-Path $dest "data\$f") -Force }
    }

    # Docs, platforms, transition
    Update-Status "Copying docs and platform specs..." "" 65
    $docsPath = Join-Path $SourceRoot "docs"
    if (Test-Path $docsPath) { Copy-Item "$docsPath\*" (Join-Path $dest "docs") -Recurse -Force -ErrorAction SilentlyContinue }
    $platPath = Join-Path $SourceRoot "platforms"
    if (Test-Path $platPath) { Copy-Item "$platPath\*" (Join-Path $dest "platforms") -Recurse -Force -ErrorAction SilentlyContinue }
    $replPath = Join-Path $SourceRoot "transition\REPLACED.md"
    if (Test-Path $replPath) { Copy-Item $replPath (Join-Path $dest "transition\REPLACED.md") -Force }

    # Panel
    if ($ChkPanel.IsChecked) {
        Update-Status "Copying panel..." "" 70
        $panelSrc = Join-Path $SourceRoot "panel"
        if (Test-Path $panelSrc) {
            Get-ChildItem $panelSrc -Exclude "node_modules" | Copy-Item -Destination (Join-Path $dest "panel") -Recurse -Force
        }
    }

    # Bridge
    if ($ChkBridge.IsChecked) {
        Update-Status "Copying bridge..." "" 75
        $bridgeSrc = Join-Path $SourceRoot "bridge"
        if (Test-Path $bridgeSrc) { Copy-Item "$bridgeSrc\*" (Join-Path $dest "bridge") -Recurse -Force }
    }

    # Installer scripts
    Copy-Item (Join-Path $SourceRoot "installer\transfer_pump.ps1") (Join-Path $dest "installer\transfer_pump.ps1") -Force -ErrorAction SilentlyContinue
    Copy-Item (Join-Path $SourceRoot "installer\validate_transfer.ps1") (Join-Path $dest "installer\validate_transfer.ps1") -Force -ErrorAction SilentlyContinue

    # MCP config snippet
    Update-Status "Generating MCP config..." "" 80
    $escaped = $dest.Replace('\', '/')
    $mcpJson = @"
{
  "mcpServers": {
    "qais": {
      "command": "python",
      "args": ["$escaped/QAIS/qais_mcp_server.py"],
      "env": { "BOND_ROOT": "$escaped" }
    },
    "iss": {
      "command": "python",
      "args": ["$escaped/ISS/iss_mcp_server.py"],
      "env": { "BOND_ROOT": "$escaped" }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-filesystem", "$escaped"]
    }
  }
}
"@
    $mcpJson | Set-Content (Join-Path $dest "installer\mcp_config_snippet.json") -Encoding ASCII
}

function Run-TransferPump {
    $dest = $InstallPath.Text

    Update-Status "Backing up v1..." "" 82
    $backupDir = Join-Path $dest "installer\v1_backup\v1_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Copy-Item (Join-Path $script:V1Path "*") $backupDir -Recurse -Force

    Update-Status "Discovering entities..." "" 85
    $frameworkEntities = @("BOND_MASTER", "PROJECT_MASTER")
    $v1Doctrine = Join-Path $script:V1Path "doctrine"
    $v2Doctrine = Join-Path $dest "doctrine"
    $entities = Get-ChildItem $v1Doctrine -Directory | Select-Object -ExpandProperty Name
    $userEntities = $entities | Where-Object { $frameworkEntities -notcontains $_ }

    Update-Status "Transferring $($userEntities.Count) entities..." "" 88
    foreach ($entity in $userEntities) {
        $src = Join-Path $v1Doctrine $entity
        $dst = Join-Path $v2Doctrine $entity
        Copy-Item $src $dst -Recurse -Force

        $ejPath = Join-Path $dst "entity.json"
        if (Test-Path $ejPath) {
            $json = Get-Content $ejPath -Raw | ConvertFrom-Json
            if ($json.PSObject.Properties.Name -contains "links") { $json.links = @() }
            if (-not ($json.PSObject.Properties.Name -contains "display_name")) {
                $json | Add-Member -NotePropertyName "display_name" -NotePropertyValue $entity
            }
            if (-not ($json.PSObject.Properties.Name -contains "public")) {
                $json | Add-Member -NotePropertyName "public" -NotePropertyValue $false
            }
            $json | ConvertTo-Json -Depth 10 | Set-Content $ejPath -Encoding UTF8
        }
        $stateDir = Join-Path $dst "state"
        if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Path $stateDir -Force | Out-Null }
    }

    Update-Status "Transferring perspective data..." "" 92
    $v1Persp = Join-Path $script:V1Path "data\perspectives"
    $v2Persp = Join-Path $dest "data\perspectives"
    if (Test-Path $v1Persp) {
        if (-not (Test-Path $v2Persp)) { New-Item -ItemType Directory -Path $v2Persp -Force | Out-Null }
        Get-ChildItem $v1Persp -Filter "*.npz" | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $v2Persp $_.Name) -Force
        }
    }
    $seedDec = Join-Path $script:V1Path "data\seed_decisions.jsonl"
    if (Test-Path $seedDec) {
        Copy-Item $seedDec (Join-Path $dest "data\seed_decisions.jsonl") -Force
    }

    Update-Status "Transferring handoffs and state..." "" 95
    $v1Handoffs = Join-Path $script:V1Path "handoffs"
    $v2Handoffs = Join-Path $dest "handoffs"
    if (Test-Path $v1Handoffs) {
        if (-not (Test-Path $v2Handoffs)) { New-Item -ItemType Directory -Path $v2Handoffs -Force | Out-Null }
        Get-ChildItem $v1Handoffs -File | ForEach-Object {
            Copy-Item $_.FullName (Join-Path $v2Handoffs $_.Name) -Force
        }
    }

    $v1Heatmap = Join-Path $script:V1Path "state\heatmap.json"
    if (Test-Path $v1Heatmap) { Copy-Item $v1Heatmap (Join-Path $dest "state\heatmap.json") -Force }

    $v1Config = Join-Path $script:V1Path "state\config.json"
    if (Test-Path $v1Config) {
        $v1Cfg = Get-Content $v1Config -Raw | ConvertFrom-Json
        $v2Cfg = @{ save_confirmation = $true; platform = "windows" }
        if ($v1Cfg.PSObject.Properties.Name -contains "save_confirmation") { $v2Cfg.save_confirmation = $v1Cfg.save_confirmation }
        if ($v1Cfg.PSObject.Properties.Name -contains "platform") { $v2Cfg.platform = $v1Cfg.platform }
        $v2Cfg | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $dest "state\config.json") -Encoding UTF8
    }

    '{"entity": null, "path": null}' | Set-Content (Join-Path $dest "state\active_entity.json") -Encoding ASCII

    # Write transfer report
    Update-Status "Writing transfer report..." "" 98
    $report = @()
    $report += "# Transfer Report"
    $report += ""
    $report += "**Timestamp:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $report += "**v1 Source:** $($script:V1Path)"
    $report += "**v2 Destination:** $dest"
    $report += "**v1 Backup:** $backupDir"
    $report += ""
    $report += "## Transferred"
    $report += ($userEntities | ForEach-Object { "- $_" }) -join "`n"
    $report += ""
    $report += "## Skipped (framework)"
    $report += ($frameworkEntities | ForEach-Object { "- $_" }) -join "`n"
    $report += ""
    $report += "v1 was NOT modified."
    Set-Content (Join-Path $dest "installer\transfer_report.md") ($report -join "`n") -Encoding ASCII
}

function Run-Install {
    Show-Page 5

    try {
        Install-Skeleton
        if ($ChkTransfer.IsChecked -and $V1BrowsePath.Text -and (Test-Path $V1BrowsePath.Text)) {
            $script:V1Path = $V1BrowsePath.Text
            Run-TransferPump
        }
        Update-Status "Done!" "Installation complete." 100
        Start-Sleep -Milliseconds 500
    } catch {
        Update-Status "Error" "Installation failed: $_" 0
        $BtnNext.Content = "Close"
        $BtnNext.Visibility = "Visible"
        return
    }

    # Populate done page
    $dest = $InstallPath.Text
    $McpSnippetPath.Text = "MCP config: $(Join-Path $dest 'installer\mcp_config_snippet.json')"
    if ($ChkTransfer.IsChecked -and $V1BrowsePath.Text) {
        $TransferReportPath.Text = "Transfer report: $(Join-Path $dest 'installer\transfer_report.md')"
    }

    Show-Page 6
}

# ── PAGE NAVIGATION ───────────────────────────────────────────

function Get-NextPage {
    $cur = $script:CurrentPage
    if ($cur -eq 3) {
        # After components, always show transfer page
        Detect-V1
        if ($script:V1Detected) {
            $V1PathText.Text = "Found existing installation at: $($script:V1Path)"
            $V1BrowsePath.Text = $script:V1Path
            $ChkTransfer.IsChecked = $true
            $V1BrowsePath.IsEnabled = $true
            $V1BrowseBtn.IsEnabled = $true
        } else {
            $V1PathText.Text = "No existing installation detected automatically."
            $V1BrowsePath.Text = ""
            $ChkTransfer.IsChecked = $false
        }
        return 4
    }
    if ($cur -eq 4) { return 5 } # transfer -> install
    return $cur + 1
}

function Get-PrevPage {
    $cur = $script:CurrentPage
    if ($cur -eq 5 -and -not $script:V1Detected) { return 3 }
    if ($cur -eq 5 -and $script:V1Detected) { return 4 }
    return $cur - 1
}

$BtnNext.Add_Click({
    $cur = $script:CurrentPage
    if ($cur -eq 6) { $window.Close(); return }

    $next = Get-NextPage
    if ($next -eq 5) { Run-Install; return }

    Show-Page $next
    if ($next -eq 1) { Check-Prerequisites }
})

$BtnBack.Add_Click({
    $prev = Get-PrevPage
    Show-Page $prev
})

$BrowseBtn.Add_Click({
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Choose BOND installation folder"
    $dialog.SelectedPath = $InstallPath.Text
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $InstallPath.Text = $dialog.SelectedPath
    }
})

# ── TRANSFER PAGE CONTROLS ────────────────────────────────────

$ChkTransfer.Add_Checked({
    $V1BrowsePath.IsEnabled = $true
    $V1BrowseBtn.IsEnabled = $true
})

$ChkTransfer.Add_Unchecked({
    $V1BrowsePath.IsEnabled = $false
    $V1BrowseBtn.IsEnabled = $false
})

$V1BrowseBtn.Add_Click({
    $dialog = New-Object System.Windows.Forms.FolderBrowserDialog
    $dialog.Description = "Select your existing BOND installation folder"
    if ($V1BrowsePath.Text -and (Test-Path $V1BrowsePath.Text)) {
        $dialog.SelectedPath = $V1BrowsePath.Text
    }
    if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $V1BrowsePath.Text = $dialog.SelectedPath
        $script:V1Path = $dialog.SelectedPath
        $script:V1Detected = $true
    }
})

# ── LAUNCH ────────────────────────────────────────────────────

Show-Page 0
$window.ShowDialog() | Out-Null
